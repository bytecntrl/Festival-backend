from dataclasses import dataclass


@dataclass
class TokenJwt:
    username: str
    role: str
    exp: int

    def __str__(self) -> str:
        return f"TokenJwt(username={self.username}, role={self.role}, exp={self.exp}, type={self.type})"
