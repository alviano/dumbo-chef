from base64 import b64decode, b64encode
from dumbo_asp.primitives import GroundAtom, Predicate, SymbolicAtom, SymbolicProgram, SymbolicRule
from dumbo_utils.validation import validate
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

import clingo


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5188", "https://asp-chef.alviano.net"],
    allow_credentials=False,
    allow_methods=["POST"],
    allow_headers=["*"],
)


def to_b64(string: str) -> str:
    return b64encode(string.encode()).decode()


def from_b64(encoded_content: str) -> str:
    return b64decode(encoded_content.encode()).decode()


def extract_b64(atom: str) -> str:
    return from_b64(SymbolicAtom.parse(atom).arguments[0].string_value())


def endpoint(path):
    def wrapper(func):
        @app.post(path)
        async def wrapped(request: Request):
            json = await request.json()
            try:
                return await func(json)
            except Exception as e:
                return {
                    "error" : str(e)
                }
        return wrapped
    return wrapper
    

@endpoint("/to-zero-simplification-version/")
async def _(json):
    program = SymbolicProgram.parse(json["program"])
    false_predicate = Predicate.parse(json["false_predicate"]).name
    extra_atoms = [GroundAtom.parse(atom) for atom in json["extra_atoms"]]

    return {
        "program": str(program.to_zero_simplification_version(false_predicate=false_predicate, extra_atoms=extra_atoms))
    }


@endpoint("/global-safe-variables/")
async def _(json):
    program = SymbolicProgram.parse(json["program"])

    return {
        "rules": [
            {
                "rule": str(rule),
                "variables": rule.global_safe_variables,
            }
            for rule in program
        ]
    }


@endpoint("/expand-global-safe-variables/")
async def _(json):
    program = SymbolicProgram.parse(json["program"])
    expand = {SymbolicRule.parse(key): value for key, value in json["expand"].items()}

    return {
        "program": str(program.expand_global_safe_variables_in_rules(expand))
    }


@endpoint("/move-up/")
async def _(json):
    program = SymbolicProgram.parse(json["program"])
    atoms = SymbolicProgram.parse(json["atoms"])

    validate("atoms", all([rule.is_fact for rule in atoms]), equals=True)
    atoms = [rule.head_atom for rule in atoms]

    return {
        "program": str(program.move_up(*atoms))
    }

