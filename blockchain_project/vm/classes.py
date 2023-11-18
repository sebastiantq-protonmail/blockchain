import compileall
import dis
import hashlib
import types
from pydantic import BaseModel

class SimpleVM(BaseModel):
    contract_states: dict = {}
    
    def deploy_contract(self, contract_code):
        """
        Deploy a new contract to the VM. 
        Returns the contract's bytecode and an address (for this example, the address is just the bytecode's hash).
        """
        # Compile the contract
        bytecode = compile(contract_code, '<string>', 'exec')
        contract_address = hashlib.sha256(contract_code.encode()).hexdigest()
        
        # Initialize the contract's state
        self.contract_states[contract_address] = {}
        
        return bytecode, contract_address

    def execute_contract(self, contract_address, bytecode, function_signature, *args, **kwargs):
        """
        Execute a function on a deployed contract.
        """
        # Check if the contract exists
        if contract_address not in self.contract_states:
            raise Exception("Contract not found!")
        
        # Prepare the environment
        contract_state = self.contract_states[contract_address]
        global_env = {
            "state": contract_state,
            "__name__": "__main__"
        }
        
        # Execute the bytecode to define the contract
        exec(bytecode, global_env)
        
        # Extract the function from the bytecode based on its signature and execute it
        if function_signature in global_env:
            function = global_env[function_signature]
            return function(*args, **kwargs)
        else:
            raise Exception(f"Function {function_signature} not found in contract!")

# Test our VM with a simple contract
contract_code = """
def increment():
    if "counter" not in state:
        state["counter"] = 0
    state["counter"] += 1
    return state["counter"]

def decrement():
    if "counter" not in state:
        state["counter"] = 0
    state["counter"] -= 1
    return state["counter"]
"""

vm = SimpleVM()
bytecode, address = vm.deploy_contract(contract_code)
result1 = vm.execute_contract(address, bytecode, "increment")
result2 = vm.execute_contract(address, bytecode, "decrement")

result1, result2