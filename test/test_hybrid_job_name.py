import pytest
from braket.jobs.hybrid_job import _validate_hybrid_job_name

@pytest.mark.parametrize("name", ["A", "job-123", "X"*50])
def test_valid_names(name):
    _validate_hybrid_job_name(name)

@pytest.mark.parametrize("name", ["", "job_case", "-leading", "trailing-", "X"*51])
def test_invalid_names(name):
    with pytest.raises(ValueError):
        _validate_hybrid_job_name(name)
