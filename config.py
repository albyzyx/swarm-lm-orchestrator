import torch
from data_structures import ModelBackendConfig, ModelChatConfig, ModelConfig, ModelFrontendConfig

default_chat_config = ModelChatConfig(
    max_session_length=8192,
    sep_token="###",
    stop_token="###",
    extra_stop_sequences=["</s>"],
    generation_params=dict(do_sample=1, temperature=0.6, top_p=0.9),
)

MODEL_FAMILIES = {
    "Llama 2": [
      
         ModelConfig(
            ModelBackendConfig(repository="stabilityai/StableBeluga-7B", aliases=["stabilityai/StableBeluga-7B"]),
            ModelFrontendConfig(
                name="Stable Beluga 2 (7B)",
                model_card="https://huggingface.co/stabilityai/StableBeluga-7B",
                license="https://huggingface.co/stabilityai/StableBeluga2-7B/blob/main/LICENSE.txt",
            ),
            default_chat_config,
        ),
      
    ],

}

INITIAL_PEERS = [
   "/ip4/130.250.185.236/tcp/32722/p2p/QmSzvetBZaMdeprswgBCLwEZtk2WjGGeXwmChmfWKPmQCK"
]

IDENTITY_PATH = "main.id"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

try:
    from cpufeature import CPUFeature

    has_avx512 = CPUFeature["AVX512f"] and CPUFeature["OS_AVX512"]
except ImportError:
    has_avx512 = False

if DEVICE == "cuda":
    TORCH_DTYPE = "auto"
elif has_avx512:
    TORCH_DTYPE = torch.bfloat16
else:
    TORCH_DTYPE = torch.float32  # You can use bfloat16 in this case too, but it will be slow

STEP_TIMEOUT = 5 * 60
