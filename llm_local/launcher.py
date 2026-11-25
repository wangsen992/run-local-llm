import subprocess
import logging

from llm_local.prog import Prog

logger = logging.getLogger(__name__)

class Launcher:
    """Server class for programs

    Manages the lifecycle for programs through subprocess. 

    - .start(): start the server, exit method after the server is ready to use. 
    - .close(): terminate the server process, clean up tmp folder and close file objects.
    - .monitor(): start monitoring state. can receive keyboard interrupt to close.
    - .serve(): a helper method that provide a one stop method

    After server started, the server should be observable through "server_info"

    """

    def __init__(self, prog: Prog):
        # program related attributes
        self.prog = prog

        # attributes held for the server class
        self.process = None
        self.is_closed = False
        
    def __del__(self):
        """Deconstructor is needed

        Deleting only the objects is not enough, must also kill the process and
        remove the temporary files from the program

        Note: this deconstructor is said that could be unreliable in terms of
        timing
        """
        logger.info("running deconstructor.")
        if not self.is_closed:
            self.close()

    def start(self, **input_kwargs):
        kwargs = dict(
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=self.prog.envs
                )
        kwargs.update(input_kwargs)
        self.process = subprocess.Popen(self.prog.command, **kwargs)
        logger.info(f"Child process started: pid={self.process.pid}")
        start_returncode = self._monitor_startup()

        if start_returncode == "success":
            logger.info("program start up complete.")
            self.prog.set_startup_complete()
        elif start_returncode == "failed":
            logger.error("program start up failed and exited")
            self.prog.cleanup()
        elif start_returncode == "timeout":
            logger.error("program start up timed out")
            self.close()

    def _monitor_startup(self) -> str:
        
        try:
            for line in self.process.stdout:
                
                # stdout are first written to the prog-specifi log file
                self.prog.log_file.write(line)

                if self.prog.is_startup_complete(line):
                    return "success"
            # If no start up string is detected after stdout is closed
            # then something is wrong
            self.process.wait()
            return "failed"
        except subprocess.TimeoutExpired as e:
            return "timeout"

    def close(self):

        # terminate the process
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.info("Subprocess did not exit in time; forcing kill")
                self.process.kill()
                self.process.wait()
            finally:
                logger.info("Subprocess exited.")

        # cleanup program specific stuff
        self.prog.cleanup()
        self.is_closed = True
    
    def monitor(self):
        """enters into an active monitoring state"""
        try:
            for line in self.process.stdout:
                self.prog.log_file.write(line)
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt caught! Stopping subprocess..")
            raise

        self.process.wait()
        if self.process.returncode != 0:
            raise subprocess.CalledProcessError(
                    returncode=self.process.returncode,
                    cmd=self.prog.command
                    )

    def serve(self):
        try:
            self.start()
            self.monitor()
        except KeyboardInterrupt:
            pass
        finally:
            self.close()



# class SlurmVLLMServer(Launcher):
#     """Extended VLLMServer that uses srun
#     """
# 
#     def __init__(self, cfg, srun_cfg):
#         super().__init__(cfg)
#         command = ["srun"]
#         srun_command = build_cli_flags(srun_cfg.flag_args, srun_cfg.kv_args)
#         command.extend(srun_command)
#         get_host_command = [
#                     "bash", "-c", 'printf "SERVER_HOST=%s\\n" "$(hostname)"; exec "$@"',
#                     "bash"
#                 ]
#         command.extend(get_host_command)
#         command.extend(self.prog.command)
#         self.prog.command = command
# 
#     def _monitor_start(self):
#         logger.info("running in slurmvllm")
#         for line in self.process.stdout:
#             self.log_file.write(line)
#             
#             if "SERVER_HOST" in line:
#                 server_id = line.strip().split("=")[1]
#                 logger.info(f"identified hostname: {server_id}")
#                 self.prog.server_info["hostname"]=server_id
#                 self.prog.update_server_info()
# 
#             if startup_str in line:
#                 logger.info("vllm server start up complete.")
#                 baseUrl=f"http://{self.prog.server_info["hostname"]}:{self.prog.server_info["port"]}/v1"
#                 logger.info(f"connect to baseUrl: {baseUrl}")
#                 self.prog.server_info["server_ready"]=True
#                 self.prog.update_server_info()
#                 return 0
# 
#         # If no start up string is detected after stdout is closed,
#         # then something is wrong
#         self.process.wait()
#         if self.process.returncode != 0:
#             raise subprocess.CalledProcessError(
#                     returncode=self.process.returncode,
#                     cmd=self.prog.command
#                     )
# 
#         raise RuntimeError(
#                 "Server exited with code 0 before reporting readiness"
#                 )

# @hydra.main(config_path="configs", config_name="server")
# def srun_app(cfg):
# 
#     server = SlurmVLLMServer(cfg.vllm, cfg.slurm)
#     server.serve()
