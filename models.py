from pydantic import BaseModel, Field, model_validator
from typing import Optional

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: Optional[str] = "user" 

class UserOut(BaseModel):
    id: str
    name: str
    email: str
    role: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginIn(BaseModel):
    email: str
    password: str

class StreamCreate(BaseModel):
    name: str
    rtsp_url: Optional[str] = None
    description: Optional[str] = None

class StreamOut(StreamCreate):
    id: str

class OverlayCreate(BaseModel):
    stream_id: Optional[str] = None
    type: str = Field(
        ...,
        pattern="^(image|text|banner)$",
        description="Overlay type: 'image', 'text', or 'banner'"
    )
    content: Optional[str] = None
    image: Optional[str] = None
    x: int = 0
    y: int = 0
    width: Optional[int] = None
    height: Optional[int] = None
    z_index: int = 0
    visible: bool = True

    @model_validator(mode="after")
    def validate_overlay_fields(self):
        if self.type == "image" and not self.content.startswith(("http://", "https://")):
            raise ValueError("For image overlays, 'content' must be a valid image URL.")
        if self.type == "text" and len(self.content.strip()) == 0:
            raise ValueError("For text overlays, 'content' cannot be empty.")
        return self

class OverlayOut(OverlayCreate):
    id: str
    owner_id: Optional[str] = None