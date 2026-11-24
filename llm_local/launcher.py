import subprocess


class Launcher:
    """Base launcher class for starting process with subprocess

        
    """

    def __init__(self):
        pass
        self.prog = "dummy"

    def start(self, **input_kwargs):
        kwargs = dict(
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=self.envs
                )
        kwargs.update(input_kwargs)
        self.process = subprocess.Popen(self.command, **kwargs)
        logger.info(f"Child process started: pid={self.process.pid}")
        self._monitor_start()

    def close(self):
        pass

    def monitor(self):
        pass

    def _monitor_start(self) -> str:
        """Returns bool only for startup success

        startup success checked from program stdout monitoring.
        If startup is successful, returns "success"
        Failure scenarios:
        - program exited during startup, never seen the startup msg.
            * returns "failed"
        - program never exited, just hanged and never produced startup msg
            * returns "timeout"
        """
        for line in self.process.stdout:
            self.log_file.write(line)

            if startup_str in line:
                logger.info(f"{self.prog} start up complete.")
                return "success"

        # If no start up string is detected after stdout is closed,
        # then something is wrong
        try:
            self.process.wait(timeout=1200)
        except subprocess.TimeoutExpired as e:
            return "timeout"

        return "failed"

