from enum import Enum
class TaskState(Enum):
    Claim = 0,
    Work = 1,
    Upload = 2,
    Complete = 3,
    Remove = 4,

class TaskItem:
    job = None
    state:TaskState
    logfile = None
    error = False
    retries = 0
    working_dir = None

    def __init__(self, job):
        self.state = TaskState.Claim
        self.job = job

    def getProjectId(self):
        if self.job is None:
            return None

        return self.job['projectId']

    def getJobId(self):
        if self.job is None:
            return None
        
        return self.job['jobId']

    def getStepNumber(self):
        if self.job is None:
            return None

        if 'step' not in self.job:
            return None

        if 'number' not in self.job['step']:
            return None


        return self.job['step']['number']

    def retriesInc(self):
        self.retries = self.retries + 1

    def retriesReset(self):
        self.retries = 0