import base64
import compileall
import marshal
import dis
import hashlib
import types
from typing import Optional
from pydantic import BaseModel

class SmartContract(BaseModel):
    """
    The SmartContract class is a contract that contains a dictionary of functions.
    """
    bytecode: Optional[str] = "" # Base64 encoded bytecode (bytes)
    state: dict = {}
    
    def extract_functions(self) -> dict:
        """
        Extract all functions from the contract's bytecode.
        """
        functions = {}
        
        # Deserialize the bytecode
        serialized_bytecode = base64.b64decode(self.bytecode)
        bytecode = marshal.loads(serialized_bytecode)

        for instruction in dis.get_instructions(bytecode):
            if instruction.opname == "LOAD_GLOBAL":
                function_name = instruction.argval
                function_code = self.extract_function_code(function_name)
                functions[function_name] = function_code
        return functions
    
    def extract_function_code(self, function_name) -> list[types.CodeType]:
        """
        Extract a function's code from the contract's bytecode.
        """
        function_code = []
        function_started = False
        
        # Deserialize the bytecode
        serialized_bytecode = base64.b64decode(self.bytecode)
        bytecode = marshal.loads(serialized_bytecode)

        for instruction in dis.get_instructions(bytecode):
            if instruction.opname == "LOAD_GLOBAL":
                if instruction.argval == function_name:
                    function_started = True
            if function_started:
                function_code.append(instruction)
            if instruction.opname == "RETURN_VALUE":
                function_started = False
        return function_code

class VM(BaseModel):
    deployed_smart_contracts: dict[str, SmartContract] = {}
    
    def deploy_contract(self, contract_code: str) -> str:
        """
        Deploy a new contract to the VM. 
        Returns the contract's bytecode and an address (for this example, the address is just the bytecode's hash).
        """
        try:
            # Compile the contract
            bytecode = compile(contract_code, '<string>', 'exec')
            serialized_bytecode = marshal.dumps(bytecode)

            # TODO: Check if the contract has already been deployed
            # TODO: Add a timestamp to the contract's bytecode to avoid collisions
            contract_address = hashlib.sha256(contract_code.encode()).hexdigest()
            
            # Encode bytecode to base64 and create a new SmartContract instance
            base64_encoded_bytecode = base64.b64encode(serialized_bytecode).decode('utf-8')
            new_contract = SmartContract(bytecode=base64_encoded_bytecode)
            self.deployed_smart_contracts[contract_address] = new_contract

            return contract_address
        except Exception as e:
            print("Error deploying contract!", e)

    def execute_contract(self, contract_address: str, function_signature: str, *args, **kwargs):
        """
        Execute a function on a deployed contract.
        """
        # Check if the contract exists
        if contract_address not in self.deployed_smart_contracts:
            raise Exception("Contract not found!")
        
        print(f"Executing contract {contract_address}...")

        # Prepare the environment
        contract_state = self.deployed_smart_contracts[contract_address].state
        global_env = {
            "state": contract_state,
            "__name__": "__main__"
        }
        
        # Decode the bytecode from base64 before deserializing
        serialized_bytecode = base64.b64decode(self.deployed_smart_contracts[contract_address].bytecode)
        bytecode = marshal.loads(serialized_bytecode)

        # Execute the bytecode to define the contract
        exec(bytecode, global_env)
        
        # Extract the function from the bytecode based on its signature and execute it
        if function_signature in global_env:
            function = global_env[function_signature]
            return function(*args, **kwargs)
        else:
            raise Exception(f"Function {function_signature} not found in contract!")