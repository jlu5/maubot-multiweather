from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper
from maubot import Plugin, MessageEvent
from maubot.handlers import command

import geopy
import jinja2
import multiweather

class ConfigurationError(Exception):
    pass

class Config(BaseProxyConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        helper.copy("command_names")
        helper.copy("backend.default")
        helper.copy("backend.forecast_days")
        helper.copy("backend.openmeteo")
        helper.copy("backend.openweathermap")
        helper.copy("backend.pirateweather")
        helper.copy("geocode_backend.default")
        helper.copy("geocode_backend.prefer_native")
        for geocode_backend in geopy.geocoders.SERVICE_TO_GEOCODER:
            helper.copy(f"geocode_backend.{geocode_backend}.init_options")
            helper.copy(f"geocode_backend.{geocode_backend}.query_args")
        helper.copy("output.custom_template")

class MultiweatherBot(Plugin):
    default_template = None
    async def start(self) -> None:
        self.config.load_and_update()
        user_agent = f'Mozilla/5.0 (compatible; maubot-multiweather {self.loader.meta.version})'
        geopy.geocoders.options.default_user_agent = user_agent

        self.default_template = await self.loader.read_file('default_output.j2')
        if not self.default_template:
            raise ValueError("Failed to load default template")
        self.default_template = self.default_template.decode('utf-8')

    @classmethod
    def get_config_class(cls):
        return Config

    def _is_weather_alias(self, cmd: str) -> bool:
        return cmd in self.config["command_names"]

    async def _location_lookup(self, location: str):
        try:
            default_geocode_backend = self.config['geocode_backend']['default']
        except KeyError as e:
            raise ConfigurationError("No default geocode backend is set") from e

        geocode_config = self.config['geocode_backend'].get(default_geocode_backend) or {}
        geocoder_args = dict(
            geocode_config.get('init_options') or {}
        )
        geocoder_args['adapter_factory'] = geopy.adapters.AioHTTPAdapter
        query_args = geocode_config.get('query_args') or {}

        geocoder_cls = geopy.geocoders.get_geocoder_for_service(default_geocode_backend)
        async with geocoder_cls(**geocoder_args) as geocoder:
            result = await geocoder.geocode(location, **query_args)
            if not result:
                raise ValueError(f"No results found for location {location!r}")
            if isinstance(result, list):
                return result[0]
            return result

    def _format(self, location: str | geopy.location.Location, weather_data) -> str:
        custom_template = self.config['output'].get('custom_template')
        template_text = custom_template or self.default_template
        forecast_days = self.config['backend']['forecast_days']

        template = jinja2.Environment(loader=jinja2.BaseLoader()).from_string(template_text)
        return template.render(
            location=location,
            weather=weather_data,
            forecast_days=forecast_days)

    @command.new(aliases=_is_weather_alias)
    @command.argument("location", pass_raw=True, required=True)
    async def weather(self, evt: MessageEvent, location: str) -> None:
        try:
            default_backend = self.config['backend']['default']
        except KeyError as e:
            raise ConfigurationError("No default weather backend is set") from e
        weather_args = dict(
            self.config['backend'].get(default_backend) or {}
        )

        if not location:
            command_names = self.config["command_names"]
            await evt.reply(f"usage: !{command_names[0]} <location>")
            return

        try:
            weather_cls = multiweather.get_backend_by_name(default_backend)
            weather_backend = weather_cls(**weather_args)

            if not weather_backend.SUPPORTS_NATIVE_GEOCODE or \
                    not self.config['geocode_backend']['prefer_native']:
                geopy_result = await self._location_lookup(location)
                self.log.debug("Resolved location %r to %r", location, geopy_result)
                resolved_location = (geopy_result.latitude, geopy_result.longitude)
                displayed_location = geopy_result
            else:
                displayed_location = resolved_location = location

            weather_data = await weather_backend.get_weather(resolved_location,
                forecast_days=self.config['backend']['forecast_days'])

            reply = self._format(displayed_location, weather_data)
            await evt.reply(reply)
        except Exception as e:
            reply = f'{e.__class__.__name__}: {e}'
            await evt.reply(reply)
            raise
