"""Pembangun model.

Seluruh pengolahan berada DI DALAM Pipeline. Ini yang mencegah kebocoran:
median untuk mengisi kolom kosong, rata-rata untuk penskalaan, dan daftar
kategori semuanya dihitung HANYA dari data yang diberikan saat fit(),
yaitu data latih.
"""
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def build_preprocessor(numeric: list, categorical: list) -> ColumnTransformer:
    """Susun pengolahan untuk kolom angka dan kolom kategori."""
    angka = Pipeline([
        ("isi", SimpleImputer(strategy="median")),
        ("skala", StandardScaler()),
    ])
    kategori = Pipeline([
        ("isi", SimpleImputer(strategy="most_frequent")),
        # handle_unknown="ignore": kategori yang baru muncul di tahun uji
        # tidak membuat prediksi gagal.
        ("ubah", OneHotEncoder(handle_unknown="ignore", drop="first",
                               sparse_output=False)),
    ])
    langkah = [("num", angka, numeric)]
    if categorical:
        langkah.append(("cat", kategori, categorical))
    return ColumnTransformer(langkah)


def build_estimator(name: str, cfg: dict):
    """Kembalikan satu model sesuai namanya."""
    seed = cfg["seed"]
    bobot = cfg["model"].get("class_weight")

    if name == "logistic_regression":
        # class_weight sengaja None. "balanced" menggeser probabilitas,
        # sehingga output berhenti menjadi PD.
        return LogisticRegression(max_iter=2000, class_weight=bobot, random_state=seed)
    if name == "random_forest":
        return RandomForestClassifier(n_estimators=200, max_depth=10, min_samples_leaf=50,
                                      class_weight=bobot, random_state=seed, n_jobs=-1)
    if name == "gradient_boosting":
        return GradientBoostingClassifier(n_estimators=200, learning_rate=0.05,
                                          max_depth=3, random_state=seed)
    raise ValueError(f"Model '{name}' tidak dikenali")


def build_pipeline(name: str, numeric: list, categorical: list, cfg: dict) -> Pipeline:
    """Rakit pengolahan dan model menjadi satu Pipeline."""
    return Pipeline([
        ("prep", build_preprocessor(numeric, categorical)),
        ("model", build_estimator(name, cfg)),
    ])