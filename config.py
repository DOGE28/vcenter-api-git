from pydantic_settings import BaseSettings

class HostSettings(BaseSettings):
    boi_host_username: str
    boi_host_password: str
    sgu_host_username: str
    sgu_host_password: str
    boi_inf_host_password: str
    class Config():
        env_file = ".env"

class VcenterSettings(BaseSettings):
    username: str
    password: str
    class Config():
        env_file = ".env2"

host_settings = HostSettings()
vcenter_settings = VcenterSettings()