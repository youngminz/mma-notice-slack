import json

from fabric.api import local

phase_map = {"development": "dev", "production": "prd"}


def grouper(iterable, n):
    iterable = iter(iterable)
    count = 0
    group = []
    while True:
        try:
            group.append(next(iterable))
            count += 1
            if count % n == 0:
                yield group
                group = []
        except StopIteration:
            if group:
                yield group
            break


def load_secrets(django_env):
    phase = phase_map[django_env]
    service = "military"

    parameter_prefix = f"{phase}.{service}."

    # 1. 모든 파라미터의 이름 목록을 가져온다.
    parameters_list = json.loads(
        local("aws ssm describe-parameters --region ap-northeast-2", capture=True)
    )["Parameters"]

    # 2. 현재 프로젝트에 필요한 파라미터만 가져온다.
    names = sorted(
        [
            parameter["Name"]
            for parameter in parameters_list
            if parameter["Name"].startswith(parameter_prefix)
        ]
    )

    # 3. 2에서 구한 파라미터의 값들을 조회한다.
    # 한 번에 10개의 파라미터를 가져올 수 있으므로 조금씩 나눠서 요청한다.
    parameters = []
    for sliced_names in grouper(names, 10):
        names_formatted = " ".join([f'"{sliced_name}"' for sliced_name in sliced_names])
        result = json.loads(
            local(
                f"aws ssm get-parameters --region ap-northeast-2 --name {names_formatted}",
                capture=True,
            )
        )["Parameters"]
        parameters += result

    # 4. 파라미터를 .env 파일에 저장한다.
    with open(".env", "w") as env_file:
        for parameter in parameters:
            name = parameter.get("Name").split(".")[2]
            value = str(parameter["Value"])

            env_file.write(f'{name}="{value}"\n')
