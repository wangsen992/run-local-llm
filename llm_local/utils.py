

def build_cli_flags(flag_args, kv_args):
    flags = ["--"+item for item in flag_args]
    kv_args_list = [[f"--{k}", f"{v}"] for k, v in kv_args.items()]
    kwargs = [item for kv_pair in kv_args_list for item in kv_pair]
    return flags + kwargs
