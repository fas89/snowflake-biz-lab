# B1 Live AI Marker

This folder intentionally does not contain a `contract.fluid.yaml`.

B1 is no longer a replay/golden scenario. The active playbook calls
`task b1:forge:ai`, which uses Gemini/OpenAI at run time, writes the live
contract into the Path B workspace, and keeps the raw provider output under the
scenario runtime directory.

See [../README.md](../README.md) for the full refresh workflow.
