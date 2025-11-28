import datetime
class Logger:
    @staticmethod
    def log(msg):
        ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"{ts} | {msg}")
Logger.log("System initialized.")
