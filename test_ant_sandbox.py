from anthropic import Anthropic

client = Anthropic()

# environment = client.beta.environments.create(
#     name="python-dev",
#     config={
#         "type": "cloud",
#         "networking": {"type": "unrestricted"},
#     },
# )

environments = client.beta.environments.list()

print(environments)

environment = client.beta.environments.retrieve('env_01FKoGfUjct4DgqpX5vAkL3w')

print(environment)

client.beta.environments.archive('env_01FKoGfUjct4DgqpX5vAkL3w')

# environment_id = environments.data[0].id

# print(f'environment_id: {environment_id}')