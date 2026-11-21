import { useState } from "react";

const API = "http://127.0.0.1:8000/api";

export default function App() {
  const [liveJobs, setLiveJobs] = useState([]);
  const [liveQuery, setLiveQuery] = useState("Data Analyst");
  const [liveLocation, setLiveLocation] = useState("India"); 
  const [file, setFile] = useState(null);
  const [candidateId, setCandidateId] = useState("");
  const [skills, setSkills] = useState([]);
  const [matches, setMatches] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [uploaded, setUploaded] = useState(false);

  async function uploadResume(e) {
    e.preventDefault();
    if (!file) return setError("Choose a PDF, DOCX, or TXT resume first.");
    setBusy(true); setError(""); setMatches([]);
    try {
      const data = new FormData();
      data.append("file", file);
      const res = await fetch(`${API}/resume/upload`, { method: "POST", body: data });
      const body = await res.json();
      if (!res.ok) throw new Error(body.detail || "Resume upload failed");
      setCandidateId(body.candidate_id);
      setSkills(body.extracted_skills || []);
      setUploaded(true);
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  async function getMatches() {
    if (!candidateId) return;
    setBusy(true); setError("");
    try {
      const res = await fetch(`${API}/recommendations/${candidateId}?top_k=10`);
      const body = await res.json();
      if (!res.ok) throw new Error(body.detail || "Could not fetch recommendations");
      setMatches(body);
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }


  async function getLiveJobs() {
  if (!candidateId) return;

  setBusy(true);
  setError("");
  setLiveJobs([]);

  try {
    const url =
      `${API}/jobs/live/${candidateId}` +
      `?query=${encodeURIComponent(liveQuery)}` +
      `&location=${encodeURIComponent(liveLocation)}` +
      `&top_k=10`;

    const res = await fetch(url);
    const body = await res.json();

    if (!res.ok) {
      throw new Error(body.detail || "Could not fetch live jobs");
    }

    setLiveJobs(body.results || []);

  } catch (err) {
    setError(err.message);
  } finally {
    setBusy(false);
  }
}

  // Dashboard statistics
  const recommendedCount = matches.length;
  const detectedSkillsCount = skills.length;
  const liveJobsCount = liveJobs.length;

  const allScores = [
    ...matches.map(item => Number(item.score) || 0),
    ...liveJobs.map(job => Number(job.score) || 0)
  ];

  const topMatchScore = allScores.length
    ? Math.max(...allScores)
    : 0;

  return <main className="shell">

    {/* NAVIGATION BAR */}
    <nav className="navbar">
      <div className="brand">
        <div className="brand-logo">C</div>
        <span>CareerMatch <strong>AI</strong></span>
      </div>

      <div className="nav-links">
        <a href="#home">Home</a>
        <a href="#recommendations">Recommendations</a>
        <a href="#live-jobs">Live Jobs</a>
      </div>

      <div className="nav-status">
        <span className="status-dot"></span>
        AI Powered
      </div>
    </nav>

    <header className="hero" id="home">
      <div className="eyebrow">CAREERMATCH AI · DEMO</div>
      <h1>Find work that matches <span>your potential.</span></h1>
      <p>Upload your resume. Our recommendation engine compares your experience with job descriptions using semantic similarity and skill overlap.</p>
    </header>

        {/* DASHBOARD STATISTICS */}
    <section className="stats-grid">

      <div className="stat-card">
        <div className="stat-icon">💼</div>
        <div className="stat-value">{recommendedCount}</div>
        <div className="stat-label">Recommended Jobs</div>
        <div className="stat-note">Personalized matches</div>
      </div>

      <div className="stat-card">
        <div className="stat-icon">🎯</div>
        <div className="stat-value">{topMatchScore.toFixed(1)}%</div>
        <div className="stat-label">Top Match Score</div>
        <div className="stat-note">Best matching opportunity</div>
      </div>

      <div className="stat-card">
        <div className="stat-icon">⚡</div>
        <div className="stat-value">{detectedSkillsCount}</div>
        <div className="stat-label">Detected Skills</div>
        <div className="stat-note">Extracted from your resume</div>
      </div>

      <div className="stat-card">
        <div className="stat-icon">🌐</div>
        <div className="stat-value">{liveJobsCount}</div>
        <div className="stat-label">Live Jobs Fetched</div>
        <div className="stat-note">From Adzuna</div>
      </div>

    </section>

    <section className="panel">
      <h2>1. Upload your resume</h2>
      <form onSubmit={uploadResume} className="upload">
        <input type="file" accept=".pdf,.docx,.txt" onChange={e => {setFile(e.target.files[0]); setUploaded(false); setMatches([]);}} />
        <button disabled={busy}>{busy ? "Processing..." : "Analyze resume"}</button>
      </form>
      <p className="hint">Supported: PDF, DOCX, TXT · Maximum 5 MB</p>
      {error && <p className="error">{error}</p>}
      {uploaded && <div className="success">Resume analyzed · Candidate ID: {candidateId}</div>}
      {skills.length > 0 && <div className="skills"><strong>Detected skills</strong><div className="chips">{skills.map(s => <span key={s}>{s}</span>)}</div></div>}
      {uploaded && <button className="primary" onClick={getMatches} disabled={busy}>Find matching jobs</button>}
    </section>

    {matches.length > 0 && <section className="results" id="recommendations">
      <div className="results-head"><div><div className="eyebrow">PERSONALIZED RESULTS</div><h2>Recommended jobs</h2></div><span>{matches.length} matches</span></div>
      {matches.map((item, i) => <article className="job" key={item.job.id}>
        <div className="job-top"><div><div className="rank">#{i + 1} MATCH</div><h3>{item.job.title}</h3><p>{item.job.company} · {item.job.location} · {item.job.work_mode}</p></div>
          <div className="score">{item.score}%<small>match score</small></div></div>
        <p className="description">{item.job.description}</p>
        <div className="score-breakdown"><span>Semantic similarity: {item.semantic_score}%</span><span>Skill overlap: {item.skill_score}%</span></div>
        <div className="skills"><strong>Matched skills</strong><div className="chips">{item.matched_skills.length ? item.matched_skills.map(s => <span key={s}>{s}</span>) : <em>No exact skill matches detected</em>}</div></div>
        <p className="explanation">{item.explanation}</p>
      </article>)}
      <p className="disclaimer">Scores are approximate recommendations, not guarantees of suitability or hiring outcomes.</p>
    </section>}

    {uploaded && (
  <section className="panel" id="live-jobs">
    <h2>2. Explore Live Job Opportunities</h2>

    <input
      type="text"
      value={liveQuery}
      onChange={e => setLiveQuery(e.target.value)}
      placeholder="Job title"
    />

    <input
      type="text"
      value={liveLocation}
      onChange={e => setLiveLocation(e.target.value)}
      placeholder="Location"
    />

    <button
      className="primary"
      onClick={getLiveJobs}
      disabled={busy}
    >
      {busy ? "Searching..." : "Find Live Jobs"}
    </button>
  </section>
)}

{liveJobs.length > 0 && (
  <section className="results" id="live-results">
    <div className="eyebrow">ADZUNA LIVE JOBS</div>
    <h2>Live Job Recommendations</h2>

    {liveJobs.map((job, i) => (
      <article className="job" key={job.apply_url || i}>

        <div className="job-top">
          <div>
            <div className="rank">#{i + 1} MATCH</div>
            <h3>{job.title}</h3>
            <p>{job.company} · {job.location}</p>
          </div>

          <div className="score">
            {job.score}%
            <small>Match score</small>
          </div>
        </div>

        <p className="description">
          {job.description}
        </p>

        <div className="score-breakdown">
          <span>Semantic: {job.semantic_score}%</span>
          <span>
  Skills: {job.skill_score == null
    ? "Not available"
    : `${job.skill_score}%`}
</span>
        </div>

        <div className="skills">
          <strong>Matched Skills</strong>
          <div className="chips">
            {job.matched_skills.map(skill => (
              <span key={skill}>{skill}</span>
            ))}
          </div>
        </div>

        <div className="skills">
          <strong>Missing Skills</strong>
          <div className="chips">
            {job.missing_skills?.length
              ? job.missing_skills.map(skill => (
                  <span key={skill}>{skill}</span>
                ))
              : <em>No missing skills detected</em>}
          </div>
        </div>

        {(job.salary_min || job.salary_max) && (
          <p>
            Salary: ₹{job.salary_min?.toLocaleString("en-IN") || "N/A"}
            {" - "}
            ₹{job.salary_max?.toLocaleString("en-IN") || "N/A"}
          </p>
        )}

        {job.apply_url && (
          <a
            href={job.apply_url}
            target="_blank"
            rel="noopener noreferrer"
            className="apply-btn"
          >
            Apply Now ↗
          </a>
        )}

      </article>
    ))}
  </section>
)}
    <footer>CareerMatch AI · Built with React, FastAPI, Sentence Transformers and SQLAlchemy</footer>
  </main>;
}
