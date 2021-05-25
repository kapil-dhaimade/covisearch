from datetime import datetime


start_time: datetime = None
measurement_on: bool = False


def start_measuring_total():
    if measurement_on is False:
        return

    global start_time
    start_time = datetime.now()
    print('Measurement starts. Timestamp: ' + start_time.isoformat())


def start_measuring_operation(operation_name: str) -> object:
    if measurement_on is False:
        return None

    operation_start_time = datetime.now()
    print('Operation \'' + operation_name + '\' starts.')
    return ElapsedTimeContext(operation_name, operation_start_time)


def stop_measuring_operation(elapsed_time_ctx):
    if elapsed_time_ctx is None:
        return

    curr_time = datetime.now()
    print('Operation \'' + elapsed_time_ctx.operation_name + '\' ends. Elapsed time: ' +
          str((curr_time - elapsed_time_ctx.operation_start_time).total_seconds() * 1000) + 'ms')


def stop_measuring_total():
    if measurement_on is False:
        return

    print('Measurement stops. Total time: ' + str((datetime.now() - start_time).total_seconds() * 1000) + 'ms')


class ElapsedTimeContext:
    def __init__(self, operation_name: str, operation_start_time: datetime):
        self.operation_start_time: datetime = operation_start_time
        self.operation_name: str = operation_name
