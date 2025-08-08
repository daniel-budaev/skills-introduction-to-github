import io
import os
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

try:
    import lasio
except ImportError as exc:
    raise SystemExit("lasio is required. Please install dependencies with: pip install -r requirements.txt") from exc


# ---------- Utilities ----------

def read_las_from_path(path: str) -> lasio.LASFile:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    return lasio.read(path)


def read_las_from_bytes(file_bytes: bytes) -> lasio.LASFile:
    buffer = io.BytesIO(file_bytes)
    return lasio.read(buffer)


def get_depth_info(las: lasio.LASFile) -> Tuple[Optional[str], Optional[str]]:
    """Return (mnemonic, unit) for the depth/index curve if available."""
    depth_mnemonic = None
    depth_unit = None
    try:
        index_curve = las.index_curve
        if index_curve is not None:
            depth_mnemonic = getattr(index_curve, "mnemonic", None)
            depth_unit = getattr(index_curve, "unit", None)
    except Exception:
        pass

    if depth_mnemonic is None:
        # Best-effort: first curve is often depth
        if len(las.curves) > 0:
            depth_mnemonic = las.curves[0].mnemonic
            depth_unit = las.curves[0].unit

    return depth_mnemonic, depth_unit


def las_to_metadata_frames(las: lasio.LASFile) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Return (well_df, params_df) dataframes for editing."""
    well_rows = []
    for item in las.well:
        well_rows.append({
            "mnemonic": item.mnemonic,
            "unit": item.unit,
            "value": item.value,
            "descr": item.descr,
        })
    well_df = pd.DataFrame(well_rows, columns=["mnemonic", "unit", "value", "descr"]).sort_values("mnemonic").reset_index(drop=True)

    param_rows = []
    for item in las.params:
        param_rows.append({
            "mnemonic": item.mnemonic,
            "unit": item.unit,
            "value": item.value,
            "descr": item.descr,
        })
    params_df = pd.DataFrame(param_rows, columns=["mnemonic", "unit", "value", "descr"]).sort_values("mnemonic").reset_index(drop=True)

    return well_df, params_df


def apply_metadata_edits(las: lasio.LASFile, well_df: pd.DataFrame, params_df: pd.DataFrame) -> None:
    """Apply edits from DataFrames back into las.well and las.params.

    Allows adding new rows and editing existing ones.
    """
    # Update Well
    existing_well_keys = {item.mnemonic for item in las.well}
    seen_well_keys = set()
    for _, row in well_df.iterrows():
        mnem = str(row.get("mnemonic", "")).strip()
        if not mnem:
            continue
        unit = str(row.get("unit", "")).strip()
        value = row.get("value", None)
        descr = str(row.get("descr", "")).strip()
        if mnem in existing_well_keys:
            itm = las.well[mnem]
            itm.unit = unit
            itm.value = value
            itm.descr = descr
        else:
            # Add new
            las.well[mnem] = lasio.LASItem(mnemonic=mnem, unit=unit, value=value, descr=descr)
        seen_well_keys.add(mnem)

    # Remove well items not present anymore (optional; conservative default: keep). Uncomment to enable removal.
    # for mnem in list(existing_well_keys - seen_well_keys):
    #     del las.well[mnem]

    # Update Params
    existing_param_keys = {item.mnemonic for item in las.params}
    seen_param_keys = set()
    for _, row in params_df.iterrows():
        mnem = str(row.get("mnemonic", "")).strip()
        if not mnem:
            continue
        unit = str(row.get("unit", "")).strip()
        value = row.get("value", None)
        descr = str(row.get("descr", "")).strip()
        if mnem in existing_param_keys:
            itm = las.params[mnem]
            itm.unit = unit
            itm.value = value
            itm.descr = descr
        else:
            las.params[mnem] = lasio.LASItem(mnemonic=mnem, unit=unit, value=value, descr=descr)
        seen_param_keys.add(mnem)

    # Optional removal similar to well
    # for mnem in list(existing_param_keys - seen_param_keys):
    #     del las.params[mnem]


def curves_metadata_to_df(las: lasio.LASFile) -> pd.DataFrame:
    rows = []
    for idx, c in enumerate(las.curves):
        rows.append({
            "order": idx,
            "mnemonic": c.mnemonic,
            "unit": c.unit,
            "descr": c.descr,
        })
    return pd.DataFrame(rows, columns=["order", "mnemonic", "unit", "descr"]).sort_values("order").reset_index(drop=True)


def apply_curves_metadata_edits(las: lasio.LASFile, edited_df: pd.DataFrame) -> None:
    """Apply edits to curves metadata, including optional mnemonic rename and order change."""
    # Build mapping from original order to new state
    edited_df = edited_df.copy()
    if "order" not in edited_df.columns:
        edited_df.insert(0, "order", range(len(edited_df)))

    # We'll reconstruct curves list and data matrix from edited order and mnemonics
    original_curves = list(las.curves)
    original_data = las.data.copy() if hasattr(las, "data") and las.data is not None else None

    # Map original mnemonics to their column index
    mnemonic_to_idx = {c.mnemonic: i for i, c in enumerate(original_curves)}

    new_curves = []
    new_mnemonics: List[str] = []

    for _, row in edited_df.sort_values("order").iterrows():
        old_mnem = str(row.get("mnemonic", "")).strip()
        unit = str(row.get("unit", "")).strip()
        descr = str(row.get("descr", "")).strip()
        if old_mnem == "":
            continue

        # If mnemonic exists in original, use its curve as base; else create new empty curve
        if old_mnem in mnemonic_to_idx:
            c = original_curves[mnemonic_to_idx[old_mnem]]
            c.unit = unit
            c.descr = descr
            new_curves.append(c)
            new_mnemonics.append(c.mnemonic)
        else:
            # New curve without data yet
            new_curve = lasio.CurveItem(mnemonic=old_mnem, unit=unit, value=None, descr=descr)
            new_curves.append(new_curve)
            new_mnemonics.append(old_mnem)

    # Apply new curves list
    las.curves = new_curves

    # If a rename occurred, ensure las.curvesdict will rebuild on write. For data matrix, reorder columns accordingly
    if original_data is not None:
        # Build new data array matching new_mnemonics order; if a mnemonic wasn't present, fill NaNs
        num_rows = original_data.shape[0]
        new_data_cols = []
        for mnem in new_mnemonics:
            if mnem in mnemonic_to_idx:
                new_data_cols.append(original_data[:, mnemonic_to_idx[mnem]])
            else:
                new_data_cols.append(np.full(shape=(num_rows,), fill_value=np.nan))
        new_matrix = np.column_stack(new_data_cols) if new_data_cols else original_data
        las.set_data(new_matrix)


def las_to_dataframe(las: lasio.LASFile) -> pd.DataFrame:
    try:
        df = las.df()
        # Ensure index name is depth mnemonic for clarity
        depth_mnemonic, _ = get_depth_info(las)
        if depth_mnemonic and df.index.name != depth_mnemonic:
            df.index.name = depth_mnemonic
        return df
    except Exception:
        # Fallback constructing manually from las.data
        if getattr(las, "data", None) is None:
            return pd.DataFrame()
        columns = [c.mnemonic for c in las.curves]
        arr = las.data
        df = pd.DataFrame(arr, columns=columns)
        # If first column is depth, set index
        if len(columns) > 0:
            df = df.set_index(columns[0], drop=True)
        return df


def apply_dataframe_edits(las: lasio.LASFile, edited_df: pd.DataFrame) -> None:
    """Apply edited data back to las object preserving column order and index."""
    # Ensure the index is part of data matrix as the first column if original had it that way
    # Rebuild matrix according to las.curves order
    df = edited_df.copy()
    df = df.sort_index()

    curve_order = [c.mnemonic for c in las.curves]

    # If index mnemonic equals first curve mnemonic, ensure index is that column
    index_name = df.index.name
    if len(curve_order) > 0 and (index_name == curve_order[0]):
        matrix_columns = [index_name] + [m for m in curve_order[1:] if m in df.columns]
        working_df = df.reset_index()[matrix_columns]
    else:
        # Put index as first column regardless
        working_df = df.reset_index()
        # Keep all columns in current curve order where available
        matrix_columns = [working_df.columns[0]] + [m for m in curve_order if m in working_df.columns]
        working_df = working_df[matrix_columns]

    # Align data types
    for col in working_df.columns:
        working_df[col] = pd.to_numeric(working_df[col], errors="coerce")

    new_matrix = working_df.to_numpy()
    las.set_data(new_matrix)


# ---------- Streamlit App ----------

st.set_page_config(page_title="LAS Viewer & Editor", layout="wide")

st.title("LAS (Log ASCII Standard) Viewer & Editor")

with st.sidebar:
    st.header("Load LAS file")
    file_uploader = st.file_uploader("Upload a .las file", type=["las"])  # file-like
    path_input = st.text_input("Or enter file path", value="")
    load_button = st.button("Load file")

    if "las" not in st.session_state:
        st.session_state.las = None
        st.session_state.source_path = None
        st.session_state._uploaded_name = None

    # Auto-load uploaded file if present
    if file_uploader is not None:
        try:
            if st.session_state.get("_uploaded_name") != file_uploader.name:
                st.session_state.las = read_las_from_bytes(file_uploader.getvalue())
                st.session_state.source_path = file_uploader.name
                st.session_state._uploaded_name = file_uploader.name
        except Exception as e:
            st.error(f"Failed to load uploaded LAS file: {e}")

    # Load from path when button pressed
    if load_button and path_input.strip():
        try:
            st.session_state.las = read_las_from_path(path_input.strip())
            st.session_state.source_path = path_input.strip()
            st.session_state._uploaded_name = None
        except Exception as e:
            st.error(f"Failed to load LAS file from path: {e}")

las: Optional[lasio.LASFile] = st.session_state.get("las")

# Strict guard to prevent None access
if not isinstance(las, lasio.LASFile):
    st.info("Load a LAS file from the sidebar to begin. Upload a file or enter a path and click Load.")
    st.stop()

# Tabs
overview_tab, curves_tab, data_tab, metadata_tab, plot_tab, export_tab = st.tabs([
    "Overview", "Curves", "Data", "Metadata", "Plot", "Export"
])

with overview_tab:
    st.subheader("File Summary")
    depth_mnemonic, depth_unit = get_depth_info(las)
    start = getattr(las, "start", None)
    stop = getattr(las, "stop", None)
    step = getattr(las, "step", None)

    cols = st.columns(3)
    cols[0].metric("Curves", f"{len(las.curves)}")
    cols[1].metric("Params", f"{len(las.params)}")
    cols[2].metric("Well Items", f"{len(las.well)}")

    st.markdown("---")
    version_val = ""
    wrap_val = ""
    try:
        if hasattr(las, "version") and las.version is not None:
            if "VERS" in las.version:
                version_val = str(getattr(las.version["VERS"], "value", las.version["VERS"]))
            if "WRAP" in las.version:
                wrap_val = str(getattr(las.version["WRAP"], "value", las.version["WRAP"]))
    except Exception:
        pass
    st.write({
        "Source": st.session_state.get("source_path"),
        "Version": version_val,
        "Wrap": wrap_val,
        "Depth Curve": depth_mnemonic,
        "Depth Unit": depth_unit,
        "Start": start,
        "Stop": stop,
        "Step": step,
        "NULL": getattr(las, "null", None),
    })

with curves_tab:
    st.subheader("Curves Metadata")
    curves_df = curves_metadata_to_df(las)
    edited_curves_df = st.data_editor(
        curves_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "order": st.column_config.NumberColumn("Order", min_value=0, step=1),
            "mnemonic": st.column_config.TextColumn("Mnemonic"),
            "unit": st.column_config.TextColumn("Unit"),
            "descr": st.column_config.TextColumn("Description"),
        },
        key="curves_editor",
    )

    apply_curves = st.button("Apply Curves Metadata Edits")
    if apply_curves:
        try:
            apply_curves_metadata_edits(las, edited_curves_df)
            st.success("Curves metadata updated.")
        except Exception as e:
            st.error(f"Failed to update curves metadata: {e}")

with data_tab:
    st.subheader("Curves Data")
    df = las_to_dataframe(las)

    if df.empty:
        st.warning("No data available in this LAS file.")
    else:
        st.caption("Tip: For very large logs, consider filtering the depth range before editing.")

        # Depth filter
        depth_index_name = df.index.name or "DEPTH"
        min_depth = float(df.index.min())
        max_depth = float(df.index.max())
        selected_min, selected_max = st.slider(
            f"Depth range ({depth_index_name})",
            min_value=min_depth,
            max_value=max_depth,
            value=(min_depth, max_depth),
            step=(max(1e-9, (max_depth - min_depth) / 1000.0)),
        )
        filtered_df = df.loc[(df.index >= selected_min) & (df.index <= selected_max)]

        edited_df = st.data_editor(
            filtered_df,
            use_container_width=True,
            num_rows="fixed",
            key="data_editor",
        )

        col_a, col_b = st.columns([1, 3])
        with col_a:
            if st.button("Apply Data Edits to LAS"):
                try:
                    # Merge edited slice back into full df before applying
                    new_full_df = df.copy()
                    new_full_df.loc[edited_df.index, edited_df.columns] = edited_df
                    apply_dataframe_edits(las, new_full_df)
                    st.success("Data updated in LAS object.")
                except Exception as e:
                    st.error(f"Failed to apply data edits: {e}")
        with col_b:
            st.caption("Data edits are applied in-memory. Use Export to save to a file.")

with metadata_tab:
    st.subheader("Version & Global Settings")
    wrap_show = "UNKNOWN"
    try:
        if hasattr(las, "version") and las.version is not None and "WRAP" in las.version:
            wrap_show = str(getattr(las.version["WRAP"], "value", las.version["WRAP"])).upper()
    except Exception:
        pass
    null_val = getattr(las, "null", None)
    c1, c2 = st.columns(2)
    c1.write({"WRAP": wrap_show})
    c2.write({"NULL": null_val})

    st.markdown("---")
    st.subheader("Well Information")
    well_df, params_df = las_to_metadata_frames(las)

    edited_well_df = st.data_editor(
        well_df,
        num_rows="dynamic",
        use_container_width=True,
        key="well_editor",
        column_config={
            "mnemonic": st.column_config.TextColumn("Mnemonic"),
            "unit": st.column_config.TextColumn("Unit"),
            "value": st.column_config.TextColumn("Value"),
            "descr": st.column_config.TextColumn("Description"),
        },
    )

    st.subheader("Parameters")
    edited_params_df = st.data_editor(
        params_df,
        num_rows="dynamic",
        use_container_width=True,
        key="params_editor",
        column_config={
            "mnemonic": st.column_config.TextColumn("Mnemonic"),
            "unit": st.column_config.TextColumn("Unit"),
            "value": st.column_config.TextColumn("Value"),
            "descr": st.column_config.TextColumn("Description"),
        },
    )

    if st.button("Apply Metadata Edits"):
        try:
            apply_metadata_edits(las, edited_well_df, edited_params_df)
            st.success("Metadata updated.")
        except Exception as e:
            st.error(f"Failed to apply metadata edits: {e}")

with plot_tab:
    st.subheader("Plot Curves vs Depth")
    df = las_to_dataframe(las)
    if df.empty:
        st.warning("No data to plot.")
    else:
        available_curves = list(df.columns)
        depth_name = df.index.name or "DEPTH"
        selected_curves = st.multiselect("Select curves to plot (X-axis)", options=available_curves, default=available_curves[: min(3, len(available_curves))])
        if selected_curves:
            fig = go.Figure()
            for curve in selected_curves:
                fig.add_trace(go.Scatter(
                    x=df[curve],
                    y=df.index,
                    mode="lines",
                    name=curve,
                ))
            fig.update_layout(
                xaxis_title="Curve Value",
                yaxis_title=f"{depth_name}",
                yaxis=dict(autorange="reversed"),
                legend_title="Curves",
                height=600,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Select at least one curve to plot.")

with export_tab:
    st.subheader("Export Edited LAS")

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        version_choice = st.selectbox("LAS Version", options=["2.0", "3.0"], index=0)
        wrap_choice = st.selectbox("Wrap", options=["YES", "NO"], index=1)
    with c2:
        null_value = st.text_input("NULL value (blank to keep)", value="")
    with c3:
        default_name = "edited.las"
        if isinstance(st.session_state.get("source_path"), str) and st.session_state["source_path"]:
            base = os.path.basename(st.session_state["source_path"]) or default_name
            name_no_ext, _ = os.path.splitext(base)
            default_name = f"{name_no_ext}_edited.las"
        export_name = st.text_input("Output filename", value=default_name)

    if st.button("Prepare Download"):
        try:
            # Apply NULL override if provided
            if null_value.strip() != "":
                try:
                    las.null = float(null_value)
                except ValueError:
                    st.warning("NULL must be numeric; keeping original value.")

            string_io = io.StringIO()
            las.write(string_io, version=float(version_choice), wrap=(wrap_choice == "YES"))
            las_text = string_io.getvalue()

            st.download_button(
                label="Download LAS file",
                data=las_text,
                file_name=export_name,
                mime="text/plain",
            )
        except Exception as e:
            st.error(f"Failed to export LAS: {e}")