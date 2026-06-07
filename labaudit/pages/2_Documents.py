"""
Documents page — list, search, upload, version, and manage documents.
"""
import streamlit as st
from datetime import date

from components.auth_guard import require_auth
from components.sidebar import render_sidebar
from components.ui_helpers import (
    inject_global_css, page_header, section_header,
    empty_state, search_filter_bar, pagination_controls, alert_banner,
)
from components.status_badge import doc_status_badge, expiry_countdown
from app.database import db_session
from app.models.document import DocumentType, DocumentStatus, ComplianceCategory
from app.services.document_service import DocumentService
from app.repositories.document_repository import DocumentRepository

st.set_page_config(page_title="Documents — LabAudit", page_icon="📁", layout="wide")

user = require_auth()
inject_global_css()
render_sidebar()
page_header("Documents", "SOPs, policies, and compliance documents", "📁")

org_id = st.session_state["org_id"]
can_write = user.is_manager_or_above

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_list, tab_upload = st.tabs(["📋 All Documents", "⬆️ Upload New"])


# ──────────────────────────────────────────────────────────────────────────────
# LIST TAB
# ──────────────────────────────────────────────────────────────────────────────
with tab_list:
    # Filters
    query, filters = search_filter_bar(
        search_key="doc_search",
        placeholder="Search by title or ref number...",
        extra_filters=[
            ("Type",       [t.value.replace("_"," ").title() for t in DocumentType], "doc_type_filter"),
            ("Status",     [s.value.replace("_"," ").title() for s in DocumentStatus], "doc_status_filter"),
            ("Department", ["Chemistry", "Microbiology", "Quality Assurance", "Management"], "doc_dept_filter"),
        ],
    )

    @st.cache_data(ttl=60, show_spinner=False)
    def load_docs(_org_id, q, dtype, dstatus, ddept, page):
        with db_session() as db:
            repo = DocumentRepository(db)
            type_val = next((t for t in DocumentType if t.value.replace("_"," ").title() == dtype), None) if dtype != "All" else None
            stat_val = next((s for s in DocumentStatus if s.value.replace("_"," ").title() == dstatus), None) if dstatus != "All" else None
            dept_val = ddept if ddept != "All" else None
            items, total = repo.search(
                _org_id, q or "",
                doc_type=type_val, department=dept_val, status=stat_val,
                page=page, page_size=15,
            )
            return items, total

    page = pagination_controls(0, 15, key="docs")  # placeholder total
    docs, total = load_docs(
        org_id, query,
        filters.get("doc_type_filter", "All"),
        filters.get("doc_status_filter", "All"),
        filters.get("doc_dept_filter", "All"),
        page,
    )

    st.caption(f"{total} document(s) found")

    if not docs:
        empty_state("No documents match your filters.", "📁")
    else:
        # Header row
        st.markdown(
            "<div style='display:grid;grid-template-columns:100px 90px 1fr 130px 80px 130px 100px;"
            "gap:8px;padding:0.4rem 0.6rem;background:#f8fafc;border-radius:8px;"
            "font-size:0.75rem;font-weight:600;color:#64748b;margin-bottom:4px;'>"
            "<span>Status</span><span>Ref</span><span>Title</span>"
            "<span>Type</span><span>Ver.</span><span>Expiry</span><span>Dept</span>"
            "</div>",
            unsafe_allow_html=True,
        )

        for doc in docs:
            with st.container(border=False):
                c1, c2, c3, c4, c5, c6, c7 = st.columns([1.1, 0.9, 4, 1.3, 0.5, 1.3, 1])
                with c1:
                    st.markdown(doc_status_badge(doc.status), unsafe_allow_html=True)
                with c2:
                    st.markdown(f"<span style='font-size:0.8rem;color:#64748b;'>{doc.doc_number or '—'}</span>", unsafe_allow_html=True)
                with c3:
                    st.markdown(f"<span style='font-size:0.88rem;font-weight:500;color:#1e293b;'>{doc.title}</span>", unsafe_allow_html=True)
                with c4:
                    st.markdown(f"<span style='font-size:0.78rem;color:#64748b;'>{doc.doc_type.value.replace('_',' ').title()}</span>", unsafe_allow_html=True)
                with c5:
                    st.markdown(f"<span style='font-size:0.8rem;color:#94a3b8;'>v{doc.version}</span>", unsafe_allow_html=True)
                with c6:
                    st.markdown(expiry_countdown(doc.expiry_date), unsafe_allow_html=True)
                with c7:
                    st.markdown(f"<span style='font-size:0.78rem;color:#64748b;'>{doc.department or '—'}</span>", unsafe_allow_html=True)

            st.markdown("<hr style='margin:2px 0;border-color:#f1f5f9;'>", unsafe_allow_html=True)

    # Refresh pagination with real total
    pagination_controls(total, 15, key="docs")


# ──────────────────────────────────────────────────────────────────────────────
# UPLOAD TAB
# ──────────────────────────────────────────────────────────────────────────────
with tab_upload:
    if not can_write:
        alert_banner("You need Manager or Admin role to upload documents.", "warning")
    else:
        with st.form("upload_doc_form", clear_on_submit=True):
            st.markdown("#### Document Details")
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("Document Title *", placeholder="e.g. SOP for pH Measurement")
                doc_number = st.text_input("Document Reference", placeholder="e.g. SOP-CH-015")
                doc_type = st.selectbox(
                    "Document Type *",
                    [t.value.replace("_", " ").title() for t in DocumentType],
                )
                department = st.selectbox(
                    "Department",
                    ["", "Chemistry", "Microbiology", "Quality Assurance", "Management", "Other"],
                )
            with col2:
                compliance_cat = st.selectbox(
                    "Compliance Category",
                    [c.value.replace("_", " ").upper() for c in ComplianceCategory],
                )
                effective_date = st.date_input("Effective Date", value=date.today())
                expiry_date    = st.date_input("Expiry Date", value=None)
                description    = st.text_area("Description", height=80)

            uploaded_file = st.file_uploader(
                "Attach file (PDF, DOCX, XLSX — max 20 MB)",
                type=["pdf", "docx", "xlsx"],
            )

            submitted = st.form_submit_button("Upload Document", type="primary")

        if submitted:
            if not title:
                st.error("Document title is required.")
            else:
                with st.spinner("Saving document..."):
                    try:
                        dtype_val = next(
                            t for t in DocumentType
                            if t.value.replace("_", " ").title() == doc_type
                        )
                        cat_val = next(
                            c for c in ComplianceCategory
                            if c.value.replace("_", " ").upper() == compliance_cat
                        )
                        file_bytes = uploaded_file.read() if uploaded_file else None
                        file_name  = uploaded_file.name  if uploaded_file else None

                        with db_session() as db:
                            svc = DocumentService(db)
                            doc = svc.create_document(
                                org_id=org_id,
                                title=title,
                                doc_type=dtype_val,
                                acting_user=user,
                                doc_number=doc_number or None,
                                description=description or None,
                                compliance_category=cat_val,
                                department=department or None,
                                expiry_date=expiry_date,
                                effective_date=effective_date,
                                file_bytes=file_bytes,
                                file_name=file_name,
                            )
                        st.success(f"✅ Document '{title}' uploaded successfully.")
                        st.cache_data.clear()
                    except Exception as e:
                        st.error(f"Failed to save document: {e}")
