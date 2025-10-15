# Steam One API

Steam One is an assignment developed by arit98

## Installation

use this command to create virtual environment

```bash
python -m venv myenv
```

next to swich to venv

```bash
.\venv\Scripts\activate
```

after that its time to installing dependencies

```bash
pip install -r .\requirements.txt
```

now you can run the project

```bash
uvicorn main:app --reload
```

## Usage

### check endpoints via postman instead of swagger:
we know fastapi provide swagger but we are using postman for this example but you can use swagger instead.

### ***you need to import "streaming apps.postman_collection.json" on postman to check all endpoints.

make sure to change config.py as this is an opensource project I am creating...
