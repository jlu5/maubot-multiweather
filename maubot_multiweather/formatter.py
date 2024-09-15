class FormatHelper():
    def __init__(self, config):
        self.config = config

    def format_temp(self, temperature) -> str:
        if temperature is None:
            return 'N/A'
        # TODO configurable order / display
        return f'{temperature.c:.1f}C / {temperature.f:.1f}F'

    @staticmethod
    def format_percentage(value):
        if value is None:
            return 'N/A'
        value *= 100
        return f'{value:.1f}%'

    def format_speed(self, speed):
        if speed is None:
            return 'N/A'
        # TODO configurable order / display
        return f'{speed.kph:.1f}km/h / {speed.mph:.1f}mph'

    def format_distance(self, distance):
        if distance is None:
            return 'N/A'
        # TODO configurable order / display
        return f'{distance.km:.1f}km / {distance.mi:.1f}mi'

    def format_precipitation(self, precipitation):
        if precipitation is None:
            return 'N/A'
        # TODO configurable order / display
        return f'{precipitation.mm:.1f}mm / {precipitation.inches:.1f}in'

    def format_angle(self, angle: int):
        """Returns wind direction (N, W, S, E, etc.) given an angle."""
        # Adapted from https://stackoverflow.com/a/7490772
        directions = ('N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW')
        if angle is None:
            return directions[0]
        angle = int(angle)
        idx = int((angle/(360/len(directions)))+.5)
        return directions[idx % len(directions)]
