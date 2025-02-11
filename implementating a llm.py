from langchain_community.llms import Ollama
from langchain.agents import create_agent, AgentType
from langchain.tools import BaseTool
from typing import Optional
from pydantic import BaseModel, Field
import requests

class LibreNmsDeviceStatusToolConfig(BaseModel):
    librenms_url: str = Field(default="")
    api_token: str = Field(default="")

class LibreNmsDeviceStatusTool(BaseTool):
    name = "librenms_device_status"
    description = "Tool for querying device status from LibreNMS"
    config: Optional[LibreNmsDeviceStatusToolConfig] = None

    def __init__(self, librenms_url: str = "", api_token: str = ""):
        super().__init__()
        self.config = LibreNmsDeviceStatusToolConfig(librenms_url=librenms_url, api_token=api_token)

    def _login(self):
        # Perform login to obtain session cookies
        login_url = f"{self.config.librenms_url}/login"
        session = requests.Session()
        login_payload = {
            'username': 'librenms',  # Replace with your actual username
            'password': 'password'   # Replace with your actual password
        }
        response = session.post(login_url, data=login_payload)
        if response.status_code == 200 and "login" not in response.url:
            return session
        else:
            raise Exception("Login failed. Please check your credentials.")

    def _run(self, device_id: str):
        headers = {'X-Auth-Token': self.config.api_token}
        session = requests.Session()

        try:
            response = session.get(f"{self.config.librenms_url}/api/v0/devices/{device_id}/status", headers=headers)
            if "login" in response.url:
                # If redirected to login, perform login and retry
                session = self._login()
                response = session.get(f"{self.config.librenms_url}/api/v0/devices/{device_id}/status", headers=headers)
            
            response.raise_for_status()
            try:
                return response.json()
            except ValueError:
                return f"Invalid JSON response: {response.text}"
        except requests.exceptions.RequestException as e:
            return f"Request failed: {e}"
        except requests.exceptions.HTTPError as e:
            return f"HTTP error occurred: {e.response.text}"

    def _arun(self, device_id: str):
        raise NotImplementedError("This tool does not support async")

# Initialize the LibreNMS Device Status Tool
librenms_tool = LibreNmsDeviceStatusTool(librenms_url="", api_token="")
llm = Ollama(model="mistral", temperature=0)

# Create the agent using the correct method
agent = create_agent(
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,  # Adjust based on your requirement
    tools=[librenms_tool],
    llm=llm,
)

# Example query to the agent
device_id = "1"  # Replace with the actual device ID you want to query
response = agent.run(f"librenms_device_status('{device_id}')")
print(response)

# Query the agent
query = f"librenms_device_status('{device_id}')"
response = agent.run(query)

# Print the response
print(response)
