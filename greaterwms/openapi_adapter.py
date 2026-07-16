import json
import os
from datetime import datetime, timedelta

import jwt
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


COMPONENT_BASE_URL = os.environ.get("GREATERWMS_COMPONENT_BASE_URL", "http://192.168.12.230:8009")
TOKEN_EXPIRES_SECONDS = 7200


def success(data):
    return JsonResponse({
        "code": 0,
        "message": "success",
        "data": data,
    })


def error(message, code=400):
    return JsonResponse({
        "code": code,
        "message": message,
        "data": {},
    }, status=400)


def beijing_now():
    return datetime.now()


def format_dt(value):
    return value.strftime("%Y-%m-%d %H:%M:%S")


@csrf_exempt
def auth_token(request):
    if request.method != "POST":
        return error("method not allowed", 405)

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return error("invalid json")

    caller_did = payload.get("callerDid") or "did:greaterwms:local"
    issued_at = beijing_now()
    expires_at = issued_at + timedelta(seconds=TOKEN_EXPIRES_SECONDS)
    access_token = jwt.encode({
        "sub": caller_did,
        "scope": "capability.read capability.invoke",
        "iat": int(datetime.utcnow().timestamp()),
        "exp": int((datetime.utcnow() + timedelta(seconds=TOKEN_EXPIRES_SECONDS)).timestamp()),
    }, settings.SECRET_KEY, algorithm="HS256")

    return success({
        "accessToken": access_token,
        "tokenType": "Bearer",
        "expiresIn": TOKEN_EXPIRES_SECONDS,
        "subjectDid": caller_did,
        "scope": "capability.read capability.invoke",
        "issuedAt": format_dt(issued_at),
        "expiresAt": format_dt(expires_at),
    })


def capabilities(request):
    if request.method != "GET":
        return error("method not allowed", 405)

    return success({
        "component": {
            "componentCode": "greaterwms",
            "componentName": "GreaterWMS",
            "componentType": "custom",
            "deployDomain": "EDGE",
            "provider": "GreaterWMS",
            "version": "2.1.48",
            "protocolVersion": "1.0",
            "baseUrl": COMPONENT_BASE_URL,
            "authPath": "/open/v1/auth/token",
            "capabilityPath": "/open/v1/capabilities",
        },
        "capabilities": [
            {
                "capabilityCode": "warehouse.list",
                "capabilityName": "仓库列表",
                "description": "读取 GreaterWMS 仓库列表",
                "version": "1.0.0",
                "invokeType": "SYNC_HTTP",
                "httpMethod": "GET",
                "path": "/warehouse/multiple/",
                "timeoutMs": 10000,
                "retryable": True,
                "idempotent": True,
                "input_params": {
                    "type": "default",
                    "id": "warehouse.list",
                    "components": [
                        {
                            "type": "number",
                            "key": "max_page",
                            "label": "每页数量",
                            "location": "query",
                            "defaultValue": 30,
                            "validate": {
                                "required": False,
                            },
                        },
                    ],
                },
                "output_params": [
                    {
                        "key": "count",
                        "label": "总数",
                        "type": "number",
                    },
                    {
                        "key": "results",
                        "label": "仓库记录",
                        "type": "array",
                        "items": {
                            "type": "object",
                            "label": "仓库",
                            "properties": [
                                {
                                    "key": "warehouse_name",
                                    "label": "仓库名称",
                                    "type": "string",
                                },
                            ],
                        },
                    },
                ],
            },
        ],
    })
