| Task | Snippet |
|---|---|
| Retrieve task results | `result = task.result()` |
| Retrieve batch results | `results = batch.results()` |
| Measurement counts | `result.measurement_counts` |
| Measurement probabilities | `result.measurement_probabilities` |
| Measured qubits | `result.measured_qubits` |
| Result-type values | `result.values` |
| Value by result type | `result.get_value_by_result_type(result_type)` |
| Compiled circuit, if returned by the provider | `result.get_compiled_circuit()` |
| Program set result entry | `program_result = result[0]`<br>`entry = program_result[0]` |
