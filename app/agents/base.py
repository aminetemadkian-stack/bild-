from abc import ABC, abstractmethod
from app.models.schemas import AgentInfo, Project, AgentResult

class DesignAgent(ABC):
    info: AgentInfo
    @abstractmethod
    def run(self, project: Project) -> AgentResult:
        raise NotImplementedError
