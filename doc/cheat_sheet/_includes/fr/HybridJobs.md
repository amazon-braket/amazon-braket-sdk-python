| Imports | `from braket.aws import AwsQuantumJob`<br>`from braket.devices import Devices`<br>`from braket.jobs import hybrid_job, save_job_result`<br>`from braket.jobs.metrics import log_metric` |
| Créer une tâche à partir d'un script | `job = AwsQuantumJob.create(Devices.Amazon.SV1, source_module="algorithm_script.py", entry_point="algorithm_script:start_here", wait_until_complete=True)` |
| Décorer un point d'entrée | `@hybrid_job(device=Devices.Amazon.SV1)`<br>`def my_job():`<br>`    return save_job_result({"theta": 0.5})` |
| Lancer la tâche (la crée) | `job = my_job()` |
| Exécuter localement sans créer de tâche AWS | `@hybrid_job(device=None, local=True)` |
| Ajouter des dépendances Python | `@hybrid_job(device=Devices.Amazon.SV1, dependencies="requirements.txt")` |
| Inclure des modules sources supplémentaires | `@hybrid_job(device=Devices.Amazon.SV1, include_modules=["my_module"])` |
| Passer des données d'entrée | `@hybrid_job(device=Devices.Amazon.SV1, input_data="s3://my-bucket/input")` |
| Utiliser une réservation | `@hybrid_job(device=Devices.IQM.Garnet, reservation_arn="<arn>")` |
| Enregistrer des métriques dans la tâche | `log_metric(metric_name="loss", value=0.123, iteration_number=0)` |
| Récupérer le résultat | `job.result()` |
| Position dans la file | `job.queue_position()` |
