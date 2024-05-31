from typing import Literal

from cnc.models.config.deploy_resource_limits import (
    DeployResourceLimits,
)
from cnc.logger import get_logger

log = get_logger(__name__)


class AWSDeployResourceLimits(DeployResourceLimits):
    provider: Literal["aws"]

    # ------------------------------
    # Properties
    # ------------------------------

    @property
    def cpu(self):
        return self.format_cpu(self.raw_cpu)

    @property
    def memory(self):
        return self.format_memory(self.raw_memory)

    # ------------------------------
    # Instance methods
    # ------------------------------

    def _format_memory_string(self, value):
        if value[-1:] == "M":
            try:
                return f"{(int(float(value[:-1])/256) + 1) * 256}"
            except Exception as e:
                log.warning(f"Unable to parse memory config for {self} | {e}")
                return "1GB"
        elif value[-1:] == "G":
            formatted_val = value.replace(" ", "")
            return f"{formatted_val}B"
        else:
            return "1GB"

    def format_memory(self, value):
        mem = self._format_memory_string(value)

        cpu_val = float(self._format_cpu_string(self.raw_cpu).split(" ")[0])
        # Get memory value and convert to MiB
        if mem[-1:] == "B":
            mem_val = float(mem[:-2]) * 1024
        else:
            mem_val = int(mem)

        # Ensure memory is enough to be compatible with cpu value
        # (see: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definition_parameters.html#task_size)
        if cpu_val == 0.25 and mem_val < 512:
            return "512"
        elif cpu_val == 0.5 and mem_val < 1024:
            return "1024"
        elif cpu_val == 1 and mem_val < 2048:
            return "2048"
        elif cpu_val == 2 and mem_val < 4096:
            return "4096"
        elif cpu_val == 4 and mem_val < 8192:
            return "8192"
        else:
            return mem

    def _format_cpu_string(self, value):
        if not value:
            return "0.5 vCPU"

        # Only allow cpu units (vCPU) for aws
        try:
            val = float(value)
            if (val <= 1) and (val % 0.25 == 0):
                return f"{val} vCPU"
            elif val < 5:
                val = int(val) + (int(val) % 2)
                return f"{val} vCPU"
            elif val <= 16 and val % 2 == 0:
                return f"{val} vCPU"
            else:
                return "0.5 vCPU"
        except Exception:
            return "0.5 vCPU"

    def format_cpu(self, value):
        cpu = self._format_cpu_string(value)

        cpu_val = float(cpu.split(" ")[0])
        mem = self._format_memory_string(self.raw_memory)
        if mem[-1:] == "B":
            mem_val = float(mem[:-2]) * 1024
        else:
            mem_val = int(mem)

        # Ensure cpu is enough to be compatible with memory value
        # (see: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definition_parameters.html#task_size)
        if mem_val > 16384 and cpu_val < 4:
            return "4 vCPU"
        elif mem_val > 8192 and cpu_val < 2:
            return "2 vCPU"
        elif mem_val > 4096 and cpu_val < 1:
            return "1 vCPU"
        elif mem_val > 2048 and cpu_val < 0.5:
            return "0.5 vCPU"
        else:
            return cpu
