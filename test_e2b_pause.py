from e2b import Sandbox



sbx = Sandbox.create()
print('Sandbox created', sbx.sandbox_id)

# Pause the sandbox
# You can save the sandbox ID in your database to resume the sandbox later
sbx.pause()
print('Sandbox paused', sbx.sandbox_id)

# Connect to the sandbox (it will automatically resume the sandbox, if paused)
same_sbx = sbx.connect()
print('Connected to the sandbox', same_sbx.sandbox_id)