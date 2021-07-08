setup:
	python -m pip install --upgrade pip
	pip install -r requirements.txt
	python ./setup.py build
	python ./setup.py install
