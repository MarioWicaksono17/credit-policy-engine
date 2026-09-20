"""Pembangun pipeline model.

Seluruh transformasi berada DI DALAM Pipeline. Ini bukan soal
kerapian -- ini yang mencegah kebocoran data.

Kalau median untuk imputasi dihitung di luar Pipeline, nilainya
berasal dari seluruh dataset termasuk data uji. Informasi dari
periode yang belum terjadi ikut masuk ke proses pelatihan.
Pipeline menjamin median hanya dihitung dari data yang diberikan
saat fit().
"""
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def build_preprocessor(numeric: list, categorical: list) -> ColumnTransformer:
    """Susun transformasi untuk kolom numerik dan kategorik."""
    numeric_steps = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])

    categorical_steps = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        # handle_unknown="ignore" penting untuk validasi out-of-time:
        # kategori yang hanya muncul di vintage baru tidak boleh
        # membuat prediksi gagal.
        ("encode", OneHotEncoder(handle_unknown="ignore", drop="first", sparse_output=False)),
    ])

    return ColumnTransformer([
        ("num", numeric_steps, numeric),
        ("cat", categorical_steps, categorical),
    ])


def build_estimator(name: str, cfg: dict):
    """Kembalikan satu estimator sesuai namanya."""
    seed = cfg["seed"]
    weight = cfg["model"].get("class_weight")

    if name == "logistic_regression":
        # class_weight sengaja None. "balanced" menaikkan recall
        # tetapi menggeser probabilitas secara sistematis, sehingga
        # output berhenti menjadi PD dan tidak bisa dikalikan
        # dengan LGD dan EAD.
        return LogisticRegression(max_iter=1000, class_weight=weight, random_state=seed)

    if name == "random_forest":
        return RandomForestClassifier(
            n_estimators=200, max_depth=10, min_samples_leaf=50,
            class_weight=weight, random_state=seed, n_jobs=-1,
        )

    if name == "gradient_boosting":
        return GradientBoostingClassifier(
            n_estimators=200, learning_rate=0.05, max_depth=3, random_state=seed,
        )

    raise ValueError(f"Model '{name}' tidak dikenali")


def build_pipeline(name: str, numeric: list, categorical: list, cfg: dict) -> Pipeline:
    """Rakit preprocessor dan estimator menjadi satu Pipeline."""
    return Pipeline([
        ("prep", build_preprocessor(numeric, categorical)),
        ("model", build_estimator(name, cfg)),
    ])