Qiskit support is provided by the separate [qiskit-braket-provider](https://github.com/qiskit-community/qiskit-braket-provider) package.

| Task | Snippet |
|---|---|
| Imports | `from qiskit_braket_provider import AWSBraketProvider` |
| Instantiate a provider | `provider = AWSBraketProvider()` |
| Instantiate a backend | `provider.get_backend(name)` |
