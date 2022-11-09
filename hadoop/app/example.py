import sys
from enum import Enum

this_module = sys.modules[__name__]


class ApplicationCommand:
    def __init__(self, path: str = None, queue: str = None):
        self.path = path
        self.queue = queue

    def build(self):
        raise NotImplementedError()

    def get_timeout_seconds(self):
        raise NotImplementedError()


class DistributedShellApp(ApplicationCommand):

    YARN_CMD = "yarn {klass} -jar {jar} {cmd}"
    KLASS = "org.apache.hadoop.yarn.applications.distributedshell.Client"
    JAR = "{path}/*hadoop-yarn-applications-distributedshell*.jar"

    def __init__(self, path: str = None, cmd: str = None, queue: str = None):
        super().__init__(path, queue)
        self.cmd = cmd or '-shell_command \"sleep 100\"'

    def build(self) -> str:
        cmd = self.YARN_CMD.format(klass=self.KLASS,
                                    jar=self.JAR.format(path=self.path),
                                    cmd=self.cmd)
        if self.queue:
            cmd += f" -queue {self.queue}"

        return cmd

    def get_timeout_seconds(self):
        raise NotImplementedError()


class MapReduceAppType(Enum):
    SLEEP = "sleep"
    PI = "pi"
    LOADGEN = "loadgen"
    RANDOM_WRITER = "randomwriter"
    TEST_MAPRED_SORT = "testmapredsort"


class MapReduceApp(ApplicationCommand):
    MAPREDUCE_JAR = "{path}/*hadoop-mapreduce-client-jobclient-*-tests.jar"
    YARN_CMD = "yarn jar {jar} {cmd}"
    SLEEP_CMD = 'sleep {jvm_switches} -m 1 -r 1 -mt 1 -rt 1'

    def __init__(self, mr_app_type: MapReduceAppType, path: str = None, cmd: str = None, queue: str = None, timeout: int = 99999999, debug: bool = False):
        super().__init__(path, queue)
        self.name = mr_app_type.value
        self.cmd = self._determine_cmd(cmd)
        self.timeout = timeout
        self.debug = debug

    @staticmethod
    def _determine_cmd(cmd):
        if not cmd:
            return MapReduceApp.SLEEP_CMD
        split_cmd = cmd.split(" ")
        cmd = split_cmd[0] + " {jvm_switches} " + " ".join(split_cmd[1:])
        return cmd

    def build(self):
        prop = ""
        if self.queue:
            prop += f" -Dmapreduce.job.queuename={self.queue}"
        jvm_switches = ""
        if self.debug:
            jvm_switches = "-Dmapreduce.reduce.log.level=DEBUG "
            jvm_switches += "-Dmapreduce.mapper.log.level=DEBUG "
            jvm_switches += "-Dyarn.app.mapreduce.am.log.level=DEBUG "
        self.cmd = self.cmd.format(jvm_switches=jvm_switches)

        final_cmd = self.YARN_CMD.format(jar=self.MAPREDUCE_JAR.format(path=self.path), cmd=self.cmd)
        return final_cmd

    def get_timeout_seconds(self):
        return self.timeout

    def __str__(self):
        return f"{self.__class__.__name__}: name: {self.name}, command: {self.cmd}"

    def __repr__(self):
        return str(self)


class Application(Enum):
    DISTRIBUTED_SHELL = DistributedShellApp.__name__
    MAPREDUCE = MapReduceApp.__name__
