from typing import Literal
from cnc.models.config.deploy_resource_limits import (
    DeployResourceLimits,
)
from cnc.logger import get_logger

log = get_logger(__name__)


class GCPDeployResourceLimits(DeployResourceLimits):
    provider: Literal["gcp"]

    # ------------------------------
    # Properties
    # ------------------------------

    @property
    def cpu(self):
        return self.raw_cpu

    @property
    def memory(self):
        return self.raw_memory

    @property
    def gke_autopilot_cpu(self):
        if self.mem_cpu_ratio > 6.5:
            num_mem_gi = self.normalized_memory
            # mem/cpu comparison is done in Gi/cores
            # => return cpu value in millicores
            return f"{int((num_mem_gi / 6.5) * 1000)}m"

        return self.cpu

    @property
    def gke_autopilot_memory(self):
        if self.mem_cpu_ratio < 1:
            num_cpu_cores = self.normalized_cpu
            # mem/cpu comparison is done in Gi/cores
            # => return memory value in bytes
            return int(num_cpu_cores * (2**30))

        return self.memory

    @property
    def mem_cpu_ratio(self):
        try:
            # (Gi/cores)
            return float(self.normalized_memory / self.normalized_cpu)
        except Exception as e:
            log.warning(
                f"Unable to normalize values for cpu: {self.cpu},"
                f" memory: {self.memory} | error: {e}"
            )

        # Return 1 here if unable to calc ratio so we just use
        # raw values for mem/cpu in that case
        return 1

    @property
    def normalized_cpu(self):
        return self.normalize_cpu_value(self.cpu)

    @property
    def normalized_memory(self):
        return self.normalize_mem_value(self.memory)

    # ------------------------------
    # Instance methods
    # ------------------------------

    def normalize_cpu_value(self, value):
        """
        returns cpu value in cores
        """
        if str(value).endswith("m"):
            return int(value[:-1]) * 1000

        return float(value)

    def normalize_mem_value(self, value):
        """
        returns memory value in Gi
        """
        memory_units = {
            "Ei": 2**60,  # Exbibytes
            "Pi": 2**50,  # Pebibytes
            "Ti": 2**40,  # Tebibytes
            "Gi": 2**30,  # Gibibytes
            "Mi": 2**20,  # Mebibytes
            "Ki": 2**10,  # Kibibytes
            "E": 10**18,  # Exabytes
            "P": 10**15,  # Petabytes
            "T": 10**12,  # Terabytes
            "G": 10**9,  # Gigabytes
            "M": 10**6,  # Megabytes
            "k": 10**3,  # Kilobytes
        }

        for unit, multiplier in memory_units.items():
            if str(value).endswith(unit):
                return float(value[: -len(unit)]) * multiplier / (2**30)
