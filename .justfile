run-test:
    PYTHONPATH=src pytest -svv 
run-test-filter TEST:
    PYTHONPATH=src pytest -svv tests/*{{TEST}}*
lint:
    ruff format src tests
    ruff check src tests --fix --exit-zero --line-length 100 --target-version py38
    
install-requirement:
    pip install -r requirements.txt
list:
    mpremote ls
upload:
    mpremote cp src/main.py :main.py
    mpremote mkdir :diy_clock || echo "Directory already exists."
    mpremote cp src/diy_clock/*.py :diy_clock/
mount_and_run:
    mpremote mount src/ run src/main.py