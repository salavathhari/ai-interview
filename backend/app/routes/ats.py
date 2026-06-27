import json
import os
import re
from io import BytesIO
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Any
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.auth.utils import get_current_user
from app.core.rate_limit import limiter
from app.models.user import User
from app.models.resume import Resume
from app.models.career import JobDescription, ResumeAnalysis, OptimizedResume
from app.models.ats_report import ATSReport
from app.services.career_service import CareerService

router = APIRouter(prefix="/ats", tags=["ATS"])


class ATSAnalyzeRequest(BaseModel):
    resume_id: int
    job_description_id: Optional[int] = None


class ATSOptimizeRequest(BaseModel):
    resume_id: int
    job_description_id: Optional[int] = None


class ATSReportResponse(BaseModel):
    id: int
    user_id: int
    overall_score: float
    keyword_score: float
    skills_score: float
    experience_score: float
    projects_score: float
    education_score: float
    formatting_score: float
    readability_score: float
    resume_parsed: Optional[str]
    jd_parsed: Optional[str]
    keyword_analysis: Optional[str]
    formatting_analysis: Optional[str]
    experience_analysis: Optional[str]
    projects_analysis: Optional[str]
    education_analysis: Optional[str]
    readability_analysis: Optional[str]
    matched_skills: Optional[str]
    missing_skills: Optional[str]
    additional_skills: Optional[str]
    recommendations: Optional[str]
    optimization_summary: Optional[str]
    is_analyzed: bool
    created_at: Any

    class Config:
        from_attributes = True


class ATSOptimizeResponse(BaseModel):
    id: int
    optimized_text: Optional[str]
    improvements: Optional[str]
    professional_summary: Optional[str]
    optimized_skills: Optional[str]
    optimized_keywords: Optional[str]
    format: str
    created_at: Any

    class Config:
        from_attributes = True


@router.post("/analyze", response_model=ATSReportResponse)
@limiter.limit("10/minute")
def analyze_ats(
    request: Request,
    body: ATSAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resume = db.query(Resume).filter(
        Resume.id == body.resume_id,
        Resume.user_id == current_user.id,
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    jd_text = None
    if body.job_description_id:
        jd = db.query(JobDescription).filter(
            JobDescription.id == body.job_description_id,
            JobDescription.user_id == current_user.id,
        ).first()
        if jd:
            jd_text = jd.raw_text

    analysis = CareerService.calculate_comprehensive_ats_score(resume.extracted_text, jd_text)

    existing_analysis = db.query(ResumeAnalysis).filter(
        ResumeAnalysis.resume_id == body.resume_id,
        ResumeAnalysis.user_id == current_user.id,
    ).order_by(ResumeAnalysis.created_at.desc()).first()

    ats_report = ATSReport(
        user_id=current_user.id,
        resume_id=body.resume_id,
        job_description_id=body.job_description_id,
        resume_analysis_id=existing_analysis.id if existing_analysis else None,
        overall_score=analysis["overall_score"],
        keyword_score=analysis["breakdown"]["keyword_match"],
        skills_score=analysis["breakdown"]["skills_match"],
        experience_score=analysis["breakdown"]["experience_match"],
        projects_score=analysis["breakdown"]["projects_relevance"],
        education_score=analysis["breakdown"]["education_match"],
        formatting_score=analysis["breakdown"]["formatting"],
        readability_score=analysis["breakdown"]["readability"],
        resume_parsed=json.dumps(analysis["resume_parsed"]),
        jd_parsed=json.dumps(analysis["jd_parsed"]) if analysis["jd_parsed"] else None,
        keyword_analysis=json.dumps(analysis["keyword_analysis"]),
        formatting_analysis=json.dumps(analysis["formatting_analysis"]),
        experience_analysis=json.dumps(analysis["experience_analysis"]),
        projects_analysis=json.dumps(analysis["projects_analysis"]),
        education_analysis=json.dumps(analysis["education_analysis"]),
        readability_analysis=json.dumps(analysis["readability_analysis"]),
        matched_skills=json.dumps(analysis["matched_skills"]),
        missing_skills=json.dumps(analysis["missing_skills"]),
        additional_skills=json.dumps(analysis["additional_skills"]),
        recommendations=json.dumps(analysis["recommendations"]),
        is_analyzed=True,
    )
    db.add(ats_report)
    db.commit()
    db.refresh(ats_report)

    if existing_analysis:
        existing_analysis.ats_score = analysis["overall_score"]
        existing_analysis.ats_breakdown = json.dumps(analysis["breakdown"])
        existing_analysis.ats_suggestions = json.dumps([r["message"] for r in analysis["recommendations"]])
        db.commit()

    # Update career readiness if it exists
    try:
        from app.models.career import CareerReadiness
        readiness = db.query(CareerReadiness).filter(
            CareerReadiness.user_id == current_user.id,
        ).order_by(CareerReadiness.created_at.desc()).first()
        if readiness:
            readiness.ats_score = analysis["overall_score"]
            all_scores = [s for s in [
                readiness.resume_match_score,
                readiness.ats_score,
                readiness.interview_score,
                readiness.coding_score,
                readiness.skill_gap_score,
            ] if s is not None]
            readiness.overall_score = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0.0
            db.commit()
    except Exception:
        pass

    return ats_report


@router.get("/report/{report_id}", response_model=ATSReportResponse)
def get_ats_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = db.query(ATSReport).filter(
        ATSReport.id == report_id,
        ATSReport.user_id == current_user.id,
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="ATS report not found")
    return report


@router.get("/history", response_model=List[ATSReportResponse])
def get_ats_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(ATSReport).filter(
        ATSReport.user_id == current_user.id,
    ).order_by(ATSReport.created_at.desc()).all()


@router.post("/optimize", response_model=ATSOptimizeResponse)
@limiter.limit("5/minute")
def optimize_resume_ats(
    request: Request,
    body: ATSOptimizeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resume = db.query(Resume).filter(
        Resume.id == body.resume_id,
        Resume.user_id == current_user.id,
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    jd_text = None
    if body.job_description_id:
        jd = db.query(JobDescription).filter(
            JobDescription.id == body.job_description_id,
            JobDescription.user_id == current_user.id,
        ).first()
        if jd:
            jd_text = jd.raw_text

    # Run ATS analysis first to get optimization context
    analysis = CareerService.calculate_comprehensive_ats_score(resume.extracted_text, jd_text)

    # Generate optimized resume
    optimization = CareerService.optimize_resume_ats(resume.extracted_text, analysis, jd_text)

    # Find or create resume_analysis
    existing_analysis = db.query(ResumeAnalysis).filter(
        ResumeAnalysis.resume_id == body.resume_id,
        ResumeAnalysis.user_id == current_user.id,
    ).order_by(ResumeAnalysis.created_at.desc()).first()

    if not existing_analysis:
        resume_analysis = CareerService.analyze_resume(resume.extracted_text, jd_text)
        existing_analysis = ResumeAnalysis(
            user_id=current_user.id,
            resume_id=body.resume_id,
            job_description_id=body.job_description_id,
            summary=resume_analysis.get("summary", ""),
            detected_skills=json.dumps(resume_analysis.get("detected_skills", [])),
            experience_level=resume_analysis.get("experience_level", ""),
            projects=json.dumps(resume_analysis.get("projects", [])),
            technologies=json.dumps(resume_analysis.get("technologies", [])),
            education=json.dumps(resume_analysis.get("education", [])),
            certifications=json.dumps(resume_analysis.get("certifications", [])),
            ats_score=analysis["overall_score"],
            ats_breakdown=json.dumps(analysis["breakdown"]),
            ats_suggestions=json.dumps([r["message"] for r in analysis["recommendations"]]),
            is_analyzed=True,
        )
        db.add(existing_analysis)
        db.commit()
        db.refresh(existing_analysis)

    # Store optimization
    optimized = OptimizedResume(
        user_id=current_user.id,
        resume_analysis_id=existing_analysis.id,
        optimized_text=optimization.get("optimized_text", resume.extracted_text),
        improvements=json.dumps(optimization.get("improvements", [])),
        professional_summary=optimization.get("professional_summary", ""),
        optimized_skills=json.dumps(optimization.get("optimized_skills", [])),
        optimized_projects=json.dumps(optimization.get("optimized_projects", [])),
        optimized_keywords=json.dumps(optimization.get("optimized_keywords", [])),
        optimized_experience=json.dumps(optimization.get("optimized_experience", [])),
        format="txt",
    )
    db.add(optimized)
    db.commit()
    db.refresh(optimized)

    # Trigger readiness recalculation after ATS optimization
    try:
        from app.services.automation_service import AutomationService
        automation = AutomationService(db)
        automation._update_readiness(current_user.id, trigger_event="ats_optimization")
    except Exception:
        pass

    return optimized


@router.get("/optimize/{optimize_id}", response_model=ATSOptimizeResponse)
def get_optimized_resume(
    optimize_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    optimized = db.query(OptimizedResume).filter(
        OptimizedResume.id == optimize_id,
        OptimizedResume.user_id == current_user.id,
    ).first()
    if not optimized:
        raise HTTPException(status_code=404, detail="Optimized resume not found")
    return optimized


@router.get("/optimize-history", response_model=List[ATSOptimizeResponse])
def get_optimize_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(OptimizedResume).filter(
        OptimizedResume.user_id == current_user.id,
    ).order_by(OptimizedResume.created_at.desc()).all()


@router.get("/report/{report_id}/download")
def download_ats_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = db.query(ATSReport).filter(
        ATSReport.id == report_id,
        ATSReport.user_id == current_user.id,
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="ATS report not found")

    # Build report text
    lines = []
    lines.append("=" * 60)
    lines.append("ATS RESUME ANALYSIS REPORT")
    lines.append("=" * 60)
    lines.append(f"Report ID: {report.id}")
    lines.append(f"Generated: {report.created_at}")
    lines.append("")

    lines.append(f"OVERALL ATS SCORE: {report.overall_score}/100")
    lines.append("")
    lines.append("SCORE BREAKDOWN:")
    lines.append(f"  Keyword Match:   {report.keyword_score}/100 (35% weight)")
    lines.append(f"  Skills Match:    {report.skills_score}/100 (20% weight)")
    lines.append(f"  Experience:      {report.experience_score}/100 (15% weight)")
    lines.append(f"  Projects:        {report.projects_score}/100 (10% weight)")
    lines.append(f"  Education:       {report.education_score}/100 (5% weight)")
    lines.append(f"  Formatting:      {report.formatting_score}/100 (10% weight)")
    lines.append(f"  Readability:     {report.readability_score}/100 (5% weight)")
    lines.append("")

    # Matched skills
    matched = json.loads(report.matched_skills) if report.matched_skills else []
    if matched:
        lines.append(f"MATCHED SKILLS ({len(matched)}):")
        for s in matched:
            lines.append(f"  + {s}")
        lines.append("")

    # Missing skills
    missing = json.loads(report.missing_skills) if report.missing_skills else []
    if missing:
        lines.append(f"MISSING SKILLS ({len(missing)}):")
        for s in missing:
            lines.append(f"  - {s}")
        lines.append("")

    # Additional skills
    additional = json.loads(report.additional_skills) if report.additional_skills else []
    if additional:
        lines.append(f"ADDITIONAL SKILLS ({len(additional)}):")
        for s in additional:
            lines.append(f"  * {s}")
        lines.append("")

    # Keyword analysis
    kw = json.loads(report.keyword_analysis) if report.keyword_analysis else {}
    if kw:
        lines.append("KEYWORD ANALYSIS:")
        lines.append(f"  Matched: {kw.get('matched_count', 0)} keywords")
        lines.append(f"  Missing: {kw.get('missing_count', 0)} keywords")
        lines.append(f"  Density: {kw.get('keyword_density', 0)}%")
        lines.append("")

    # Formatting
    fmt = json.loads(report.formatting_analysis) if report.formatting_analysis else {}
    if fmt:
        lines.append(f"FORMATTING SCORE: {fmt.get('score', 0)}/100")
        for issue in fmt.get("issues", []):
            lines.append(f"  ! {issue}")
        lines.append("")

    # Recommendations
    recs = json.loads(report.recommendations) if report.recommendations else []
    if recs:
        lines.append("RECOMMENDATIONS:")
        for rec in recs:
            priority = rec.get("priority", "").upper()
            lines.append(f"  [{priority}] {rec.get('message', '')}")
            if rec.get("impact"):
                lines.append(f"          Impact: {rec['impact']}")
        lines.append("")

    lines.append("=" * 60)
    lines.append("END OF REPORT")
    lines.append("=" * 60)

    report_text = "\n".join(lines)

    return StreamingResponse(
        BytesIO(report_text.encode("utf-8")),
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=ats_report_{report.id}.txt"},
    )


@router.get("/optimize/{optimize_id}/download")
def download_optimized_resume(
    optimize_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    optimized = db.query(OptimizedResume).filter(
        OptimizedResume.id == optimize_id,
        OptimizedResume.user_id == current_user.id,
    ).first()
    if not optimized:
        raise HTTPException(status_code=404, detail="Optimized resume not found")

    return StreamingResponse(
        BytesIO((optimized.optimized_text or "").encode("utf-8")),
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=optimized_resume_{optimize_id}.txt"},
    )


# ------------------------------------------------------------------
# Format-Preserving DOCX/PDF Optimization Endpoints
# ------------------------------------------------------------------

@router.post("/optimize-docx")
@limiter.limit("5/minute")
def optimize_resume_format_preserving(
    request: Request,
    body: ATSOptimizeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Optimize resume preserving original DOCX formatting. Returns DOCX bytes."""
    resume = db.query(Resume).filter(
        Resume.id == body.resume_id,
        Resume.user_id == current_user.id,
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if not resume.file_path or not os.path.exists(resume.file_path):
        raise HTTPException(status_code=400, detail="Original resume file not found on server")

    jd_text = None
    if body.job_description_id:
        jd = db.query(JobDescription).filter(
            JobDescription.id == body.job_description_id,
            JobDescription.user_id == current_user.id,
        ).first()
        if jd:
            jd_text = jd.raw_text

    analysis = CareerService.calculate_comprehensive_ats_score(resume.extracted_text, jd_text)

    try:
        docx_bytes = CareerService.optimize_docx_format_preserving(
            resume.file_path, resume.extracted_text, analysis, jd_text
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DOCX optimization failed: {str(e)}")

    # Store optimization record
    optimization = CareerService.optimize_resume_ats(resume.extracted_text, analysis, jd_text)

    existing_analysis = db.query(ResumeAnalysis).filter(
        ResumeAnalysis.resume_id == body.resume_id,
        ResumeAnalysis.user_id == current_user.id,
    ).order_by(ResumeAnalysis.created_at.desc()).first()

    if not existing_analysis:
        resume_analysis = CareerService.analyze_resume(resume.extracted_text, jd_text)
        existing_analysis = ResumeAnalysis(
            user_id=current_user.id,
            resume_id=body.resume_id,
            job_description_id=body.job_description_id,
            summary=resume_analysis.get("summary", ""),
            detected_skills=json.dumps(resume_analysis.get("detected_skills", [])),
            experience_level=resume_analysis.get("experience_level", ""),
            projects=json.dumps(resume_analysis.get("projects", [])),
            technologies=json.dumps(resume_analysis.get("technologies", [])),
            education=json.dumps(resume_analysis.get("education", [])),
            certifications=json.dumps(resume_analysis.get("certifications", [])),
            ats_score=analysis["overall_score"],
            ats_breakdown=json.dumps(analysis["breakdown"]),
            ats_suggestions=json.dumps([r["message"] for r in analysis["recommendations"]]),
            is_analyzed=True,
        )
        db.add(existing_analysis)
        db.commit()
        db.refresh(existing_analysis)

    # Store optimized text
    optimized = OptimizedResume(
        user_id=current_user.id,
        resume_analysis_id=existing_analysis.id,
        optimized_text=optimization.get("optimized_text", resume.extracted_text),
        improvements=json.dumps(optimization.get("improvements", [])),
        professional_summary=optimization.get("professional_summary", ""),
        optimized_skills=json.dumps(optimization.get("optimized_skills", [])),
        optimized_projects=json.dumps(optimization.get("optimized_projects", [])),
        optimized_keywords=json.dumps(optimization.get("optimized_keywords", [])),
        optimized_experience=json.dumps(optimization.get("optimized_experience", [])),
        format="docx",
    )
    db.add(optimized)
    db.commit()
    db.refresh(optimized)

    # Save DOCX to temp file for later download
    docx_dir = os.path.join("uploads", "optimized")
    os.makedirs(docx_dir, exist_ok=True)
    docx_path = os.path.join(docx_dir, f"optimized_{optimized.id}.docx")
    with open(docx_path, "wb") as f:
        f.write(docx_bytes)

    score_calc = CareerService.calculate_before_after_score(
        resume.extracted_text, optimization.get("optimized_text", ""), analysis, jd_text
    )

    # Trigger readiness recalculation
    try:
        from app.services.automation_service import AutomationService
        automation = AutomationService(db)
        automation._update_readiness(current_user.id, trigger_event="ats_optimization")
    except Exception:
        pass

    return {
        "optimize_id": optimized.id,
        "format": "docx",
        "ats_before": score_calc["before"],
        "ats_after": score_calc["after"],
        "improvement": score_calc["improvement"],
        "improvements": optimization.get("improvements", []),
        "optimized_text": optimization.get("optimized_text", ""),
        "message": "Format-preserving DOCX optimization complete",
    }


@router.post("/optimize-pdf")
@limiter.limit("5/minute")
def optimize_resume_to_pdf(
    request: Request,
    body: ATSOptimizeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Optimize resume and return as PDF."""
    resume = db.query(Resume).filter(
        Resume.id == body.resume_id,
        Resume.user_id == current_user.id,
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    jd_text = None
    if body.job_description_id:
        jd = db.query(JobDescription).filter(
            JobDescription.id == body.job_description_id,
            JobDescription.user_id == current_user.id,
        ).first()
        if jd:
            jd_text = jd.raw_text

    analysis = CareerService.calculate_comprehensive_ats_score(resume.extracted_text, jd_text)
    optimization = CareerService.optimize_resume_ats(resume.extracted_text, analysis, jd_text)
    optimized_text = optimization.get("optimized_text", resume.extracted_text)

    try:
        if resume.file_path and os.path.exists(resume.file_path) and resume.file_path.endswith(".docx"):
            docx_bytes = CareerService.optimize_docx_format_preserving(
                resume.file_path, resume.extracted_text, analysis, jd_text
            )
            pdf_bytes = CareerService.docx_to_pdf(docx_bytes)
        else:
            # Build PDF from optimized text directly
            pdf_bytes = CareerService.docx_to_pdf(b"")
            # Use text-based PDF generation
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import inch
            import io as _io

            output = _io.BytesIO()
            pdf_doc = SimpleDocTemplate(output, pagesize=letter,
                rightMargin=0.5*inch, leftMargin=0.5*inch,
                topMargin=0.5*inch, bottomMargin=0.5*inch)
            styles = getSampleStyleSheet()
            story = []
            for line in optimized_text.split("\n"):
                safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                if not safe.strip():
                    story.append(Spacer(1, 4))
                elif safe.strip().isupper() or (len(safe.strip()) < 60 and safe.strip().replace(" ", "").isupper()):
                    story.append(Spacer(1, 6))
                    story.append(Paragraph(safe, styles["Heading2"]))
                else:
                    story.append(Paragraph(safe, styles["Normal"]))
            pdf_doc.build(story)
            output.seek(0)
            pdf_bytes = output.getvalue()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=optimized_resume.pdf"},
    )


@router.get("/optimize/{optimize_id}/download-docx")
def download_optimized_docx(
    optimize_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Download the format-preserved optimized DOCX."""
    optimized = db.query(OptimizedResume).filter(
        OptimizedResume.id == optimize_id,
        OptimizedResume.user_id == current_user.id,
    ).first()
    if not optimized:
        raise HTTPException(status_code=404, detail="Optimized resume not found")

    docx_path = os.path.join("uploads", "optimized", f"optimized_{optimize_id}.docx")
    if not os.path.exists(docx_path):
        # Regenerate from optimized text if file not found
        raise HTTPException(status_code=404, detail="Optimized DOCX file not found. Please re-optimize.")

    with open(docx_path, "rb") as f:
        docx_bytes = f.read()

    return StreamingResponse(
        BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename=optimized_resume_{optimize_id}.docx"},
    )


@router.get("/optimize/{optimize_id}/download-pdf")
def download_optimized_pdf(
    optimize_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Download the optimized resume as PDF."""
    optimized = db.query(OptimizedResume).filter(
        OptimizedResume.id == optimize_id,
        OptimizedResume.user_id == current_user.id,
    ).first()
    if not optimized:
        raise HTTPException(status_code=404, detail="Optimized resume not found")

    docx_path = os.path.join("uploads", "optimized", f"optimized_{optimize_id}.docx")
    if os.path.exists(docx_path):
        with open(docx_path, "rb") as f:
            docx_bytes = f.read()
        pdf_bytes = CareerService.docx_to_pdf(docx_bytes)
    else:
        # Generate PDF from text
        optimized_text = optimized.optimized_text or ""
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        import io as _io

        output = _io.BytesIO()
        pdf_doc = SimpleDocTemplate(output, pagesize=letter,
            rightMargin=0.5*inch, leftMargin=0.5*inch,
            topMargin=0.5*inch, bottomMargin=0.5*inch)
        styles = getSampleStyleSheet()
        story = []
        for line in optimized_text.split("\n"):
            safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            if not safe.strip():
                story.append(Spacer(1, 4))
            elif safe.strip().isupper():
                story.append(Spacer(1, 6))
                story.append(Paragraph(safe, styles["Heading2"]))
            else:
                story.append(Paragraph(safe, styles["Normal"]))
        pdf_doc.build(story)
        output.seek(0)
        pdf_bytes = output.getvalue()

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=optimized_resume_{optimize_id}.pdf"},
    )
