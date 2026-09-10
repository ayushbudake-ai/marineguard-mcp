# MarineGuard — V1 Test-Set Manifest

# Dataset

- Version: `v1`
- Dataset: MarineGuard V1
- Total images: 18,073
- Total validated boxes: 46,209
- Classes: 50

## Split

| Split | Images |
|---|---:|
| Train | 12,652 |
| Validation | 3,613 |
| Test | 1,808 |

## Test-set rule

The 1,808-image test split is held out from model development and is used only for controlled evaluation.

## Dataset configuration

`data/processed/marineguard/data.yaml`

## V1 test result

| Metric | Result |
|---|---:|
| Precision | 89.70% |
| Recall | 71.90% |
| Calculated F1 | 79.94% |
| mAP50 | 80.69% |
| mAP50-95 | 55.74% |
| Test images | 1,808 |

## Evaluation script

`evaluate_test.py`

The script resolves repository paths using `Path(__file__).resolve().parent`.

## Freeze rule

The V1 test split and reported V1 results must not be overwritten by experimental V2 results.
