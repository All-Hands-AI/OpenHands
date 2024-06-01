from collections import namedtuple

from opendevin.core.schema import CancellableStream

ExecResult = namedtuple('ExecResult', 'exit_code,output')
""" A result of Container.exec_run with the properties ``exit_code`` and
    ``output``. """


class DockerExecCancellableStream(CancellableStream):
    # Reference: https://github.com/docker/docker-py/issues/1989
    def __init__(self, _client, _id, _output):
        super().__init__(self.read_output())
        self._id = _id
        self._client = _client
        self._output = _output

    def close(self):
        self.closed = True

    def exit_code(self):
        return self.inspect()['ExitCode']

    def inspect(self):
        return self._client.api.exec_inspect(self._id)

    def read_output(self):
        for chunk in self._output:
            yield chunk.decode('utf-8')


def container_exec_run(
    container,
    cmd,
    stdout=True,
    stderr=True,
    stdin=False,
    tty=False,
    privileged=False,
    user='',
    detach=False,
    stream=False,
    socket=False,
    environment=None,
    workdir=None,
) -> ExecResult:
    exec_id = container.client.api.exec_create(
        container.id,
        cmd,
        stdout=stdout,
        stderr=stderr,
        stdin=stdin,
        tty=tty,
        privileged=privileged,
        user=user,
        environment=environment,
        workdir=workdir,
    )['Id']

    output = container.client.api.exec_start(
        exec_id, detach=detach, tty=tty, stream=stream, socket=socket
    )

    if stream:
        return ExecResult(
            None, DockerExecCancellableStream(container.client, exec_id, output)
        )

    if socket:
        return ExecResult(None, output)

    return ExecResult(container.client.api.exec_inspect(exec_id)['ExitCode'], output)
