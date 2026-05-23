// File: Client/src/App.jsx

import { useEffect, useMemo, useState } from 'react'
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Brain,
  CalendarDays,
  CheckCircle2,
  CircleDot,
  ClipboardCheck,
  Clock3,
  Database,
  FileText,
  HeartPulse,
  Hospital,
  LayoutDashboard,
  LockKeyhole,
  LogOut,
  MapPin,
  MessageCircle,
  PlayCircle,
  Radar,
  RefreshCw,
  Send,
  ShieldCheck,
  Sparkles,
  Star,
  Stethoscope,
  UserRound,
  Wifi,
  WifiOff,
} from 'lucide-react'
import { api } from './services/api'

const DEFAULT_PROFILE = {
  age: '',
  gender: '',
  occupation: '',
  sleep_hours: '',
  social_support: '',
  life_events: [],
}

const DEMO_PROFILE = {
  age: 22,
  gender: 'other',
  occupation: 'student',
  sleep_hours: 6,
  social_support: 'medium',
  life_events: ['final exams', 'placement preparation'],
}

const SCORE_OPTIONS = {
  0: 'Not at all',
  1: 'Several days',
  2: 'More than half the days',
  3: 'Nearly every day',
}

const PHQ9_QUESTIONS = {
  1: 'Little interest or pleasure in doing things',
  2: 'Feeling down, depressed, or hopeless',
  3: 'Trouble falling or staying asleep, or sleeping too much',
  4: 'Feeling tired or having little energy',
  5: 'Poor appetite or overeating',
  6: 'Feeling bad about yourself, or that you are a failure',
  7: 'Trouble concentrating on things',
  8: 'Moving or speaking slowly, or being unusually restless',
  9: 'Thoughts that you would be better off dead, or of hurting yourself',
}

const DEMO_CLINICS = [
  {
    name: 'NIMHANS Centre for Wellbeing',
    type: 'Mental health institute',
    distance: '6.2 km',
    rating: '4.5',
    address: 'Hosur Road, Bengaluru',
    nextSlot: 'Tomorrow, 11:30 AM',
  },
  {
    name: 'Mind and Mood Clinic',
    type: 'Psychologist and psychiatrist',
    distance: '3.8 km',
    rating: '4.7',
    address: 'Indiranagar, Bengaluru',
    nextSlot: 'Today, 6:00 PM',
  },
  {
    name: 'Calm Space Therapy',
    type: 'Counselling clinic',
    distance: '5.1 km',
    rating: '4.6',
    address: 'Koramangala, Bengaluru',
    nextSlot: 'Saturday, 10:00 AM',
  },
]

const ROADMAP_ITEMS = [
  {
    title: 'Completed backend',
    items: ['JWT register/login/refresh/logout', 'Profile service', 'PHQ-9 scoring and history'],
    icon: CheckCircle2,
    tone: 'emerald',
  },
  {
    title: 'Frontend demo',
    items: ['Auth screen', 'Onboarding form', 'PHQ-9 chat', 'Report and clinic views'],
    icon: LayoutDashboard,
    tone: 'indigo',
  },
  {
    title: 'Next backend phase',
    items: ['RAG report service', 'Google Maps API', 'Feedback persistence'],
    icon: Radar,
    tone: 'amber',
  },
]

const NAV_ITEMS = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'profile', label: 'Onboarding', icon: UserRound },
  { id: 'assessment', label: 'Assessment', icon: MessageCircle },
  { id: 'report', label: 'Report', icon: FileText },
  { id: 'clinics', label: 'Clinics', icon: Hospital },
  { id: 'feedback', label: 'Feedback', icon: CalendarDays },
]

const emptyAssessment = {
  started: false,
  answers: [],
  messages: [],
  currentQuestionId: null,
  scoreOptions: SCORE_OPTIONS,
  isComplete: false,
  needsAnswer: false,
  result: null,
  crisisSupport: null,
  notes: '',
  busy: false,
  error: '',
}

const cx = (...classes) => classes.filter(Boolean).join(' ')

const getQuestionMessage = (questionId) =>
  `Over the last 2 weeks, how often have you been bothered by: ${PHQ9_QUESTIONS[questionId]}?`

const severityFromScore = (score) => {
  if (score <= 4) return 'minimal'
  if (score <= 9) return 'mild'
  if (score <= 14) return 'moderate'
  if (score <= 19) return 'moderately_severe'
  return 'severe'
}

const formatSeverity = (severity) => {
  if (!severity) return 'Not started'
  return severity.replace('_', ' ')
}

const buildCrisisSupport = (clinicalRisk) => {
  if (!clinicalRisk) return null

  return {
    crisis_detected: true,
    message:
      'Your answer suggests possible self-harm risk. Please contact emergency services or a crisis helpline now, and reach out to someone you trust.',
    resources: [
      { name: 'iCall India', contact: '9152987821', region: 'India' },
      { name: 'Vandrevala Foundation', contact: '1860-2662-345', region: 'India' },
      {
        name: 'Local emergency services',
        contact: 'Contact your local emergency number immediately if you are in immediate danger',
        region: 'Local',
      },
    ],
  }
}

const buildRecommendation = (severity, clinicalRisk, needsFollowUp) => {
  if (clinicalRisk) {
    return 'Your responses suggest possible immediate safety concerns. Please contact local emergency services or a crisis helpline now, and share this screening with a trusted clinician.'
  }

  if (needsFollowUp) {
    return `Your PHQ-9 result falls in the ${formatSeverity(
      severity,
    )} range. Please schedule a professional mental health follow-up and continue regular check-ins.`
  }

  return 'Your responses are currently in a lower-severity range. Keep practicing daily self-care and repeat this check-in if symptoms increase.'
}

const scorePhq9 = (answers) => {
  const totalScore = answers.reduce((sum, answer) => sum + Number(answer.score || 0), 0)
  const severity = severityFromScore(totalScore)
  const questionNine = answers.find((answer) => Number(answer.question_id) === 9)
  const clinicalRisk = Number(questionNine?.score || 0) > 0
  const needsFollowUp = totalScore >= 10 || clinicalRisk

  return {
    total_score: totalScore,
    severity,
    needs_to_follow: needsFollowUp,
    clinical_risk: clinicalRisk,
    recommendation: buildRecommendation(severity, clinicalRisk, needsFollowUp),
    crisis_support: buildCrisisSupport(clinicalRisk),
  }
}

const buildDemoStart = () => ({
  answers: [],
  current_question_id: 1,
  assistant_message: getQuestionMessage(1),
  score_options: SCORE_OPTIONS,
  is_complete: false,
  needs_answer: true,
  result: null,
  crisis_support: null,
})

const continueDemoConversation = (answers, score) => {
  const nextAnswers = [...answers, { question_id: answers.length + 1, score }]

  if (nextAnswers.length >= 9) {
    const result = scorePhq9(nextAnswers)

    return {
      answers: nextAnswers,
      current_question_id: null,
      assistant_message: 'PHQ-9 assessment complete.',
      score_options: SCORE_OPTIONS,
      is_complete: true,
      needs_answer: false,
      result,
      crisis_support: result.crisis_support,
    }
  }

  const nextQuestionId = nextAnswers.length + 1

  return {
    answers: nextAnswers,
    current_question_id: nextQuestionId,
    assistant_message: getQuestionMessage(nextQuestionId),
    score_options: SCORE_OPTIONS,
    is_complete: false,
    needs_answer: true,
    result: null,
    crisis_support: null,
  }
}

const normalizeScoreOptions = (options) =>
  Object.entries(options || SCORE_OPTIONS).map(([value, label]) => ({
    value: Number(value),
    label,
  }))

const toHistoryItem = (result, notes) => ({
  assessment_id: `frontend-${Date.now()}`,
  assessment_type: 'phq9',
  total_score: result.total_score,
  severity: result.severity,
  needs_to_follow: result.needs_to_follow,
  clinical_risk: result.clinical_risk,
  recommendation: result.recommendation,
  notes: notes || null,
  crisis_support: result.crisis_support || null,
  created_at: new Date().toISOString(),
})

const Button = ({ children, className, variant = 'primary', type = 'button', ...props }) => {
  const variants = {
    primary: 'bg-stone-950 text-white hover:bg-stone-800 disabled:bg-stone-300',
    secondary: 'border border-stone-300 bg-white text-stone-900 hover:bg-stone-50 disabled:text-stone-400',
    soft: 'bg-teal-50 text-teal-800 hover:bg-teal-100 disabled:bg-stone-100 disabled:text-stone-400',
    danger: 'bg-rose-600 text-white hover:bg-rose-700 disabled:bg-rose-200',
  }

  return (
    <button
      type={type}
      className={cx(
        'inline-flex min-h-10 items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition focus:outline-none focus:ring-2 focus:ring-stone-900 focus:ring-offset-2 disabled:cursor-not-allowed',
        variants[variant],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  )
}

const StatusPill = ({ children, tone = 'stone', icon: Icon }) => {
  const tones = {
    emerald: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
    indigo: 'bg-indigo-50 text-indigo-700 ring-indigo-200',
    amber: 'bg-amber-50 text-amber-800 ring-amber-200',
    rose: 'bg-rose-50 text-rose-700 ring-rose-200',
    stone: 'bg-stone-100 text-stone-700 ring-stone-200',
    teal: 'bg-teal-50 text-teal-700 ring-teal-200',
  }

  return (
    <span
      className={cx(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold capitalize ring-1',
        tones[tone],
      )}
    >
      {Icon ? <Icon className="h-3.5 w-3.5" /> : null}
      {children}
    </span>
  )
}

const Panel = ({ title, eyebrow, action, children, className, dark = false }) => {
  const hasCustomBackground = className?.includes('bg-')
  const hasCustomBorder = className?.includes('border-')

  return (
    <section
      className={cx(
        'rounded-lg border p-5 shadow-sm',
        !hasCustomBorder && 'border-stone-200',
        !hasCustomBackground && 'bg-white',
        className,
      )}
    >
    {(title || eyebrow || action) && (
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          {eyebrow ? (
            <p className={cx('text-xs font-semibold uppercase tracking-wide', dark ? 'text-stone-300' : 'text-stone-500')}>
              {eyebrow}
            </p>
          ) : null}
          {title ? <h2 className={cx('mt-1 text-lg font-bold', dark ? 'text-white' : 'text-stone-950')}>{title}</h2> : null}
        </div>
        {action}
      </div>
    )}
    {children}
  </section>
  )
}

const Metric = ({ label, value, icon: Icon, tone = 'teal' }) => {
  const tones = {
    teal: 'bg-teal-50 text-teal-700',
    indigo: 'bg-indigo-50 text-indigo-700',
    amber: 'bg-amber-50 text-amber-700',
    rose: 'bg-rose-50 text-rose-700',
  }

  return (
    <div className="rounded-lg border border-stone-200 bg-white p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-medium text-stone-500">{label}</p>
        <span className={cx('rounded-lg p-2', tones[tone])}>
          <Icon className="h-4 w-4" />
        </span>
      </div>
      <p className="mt-3 text-2xl font-bold text-stone-950">{value}</p>
    </div>
  )
}

const AuthPanel = ({ apiOnline, authError, busy, onDemo, onSubmit }) => {
  const [mode, setMode] = useState('login')
  const [email, setEmail] = useState('demo@mindbridge.app')
  const [password, setPassword] = useState('MindBridge123')

  const handleSubmit = (event) => {
    event.preventDefault()
    onSubmit(mode, { email, password })
  }

  return (
    <Panel dark className="border-stone-800 bg-stone-950 text-white" eyebrow="Access" title="Start the MindBridge workspace">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid gap-2 rounded-lg bg-white/10 p-1 sm:grid-cols-2">
          <button
            type="button"
            onClick={() => setMode('login')}
            className={cx(
              'rounded-md px-3 py-2 text-sm font-semibold transition',
              mode === 'login' ? 'bg-white text-stone-950' : 'text-stone-300 hover:text-white',
            )}
          >
            Login
          </button>
          <button
            type="button"
            onClick={() => setMode('register')}
            className={cx(
              'rounded-md px-3 py-2 text-sm font-semibold transition',
              mode === 'register' ? 'bg-white text-stone-950' : 'text-stone-300 hover:text-white',
            )}
          >
            Signup
          </button>
        </div>

        <label className="block">
          <span className="text-sm font-medium text-stone-200">Email</span>
          <input
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="mt-2 w-full rounded-lg border border-white/20 bg-white px-3 py-2 text-sm text-stone-950 outline-none focus:ring-2 focus:ring-teal-300"
            type="email"
            required
          />
        </label>

        <label className="block">
          <span className="text-sm font-medium text-stone-200">Password</span>
          <input
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="mt-2 w-full rounded-lg border border-white/20 bg-white px-3 py-2 text-sm text-stone-950 outline-none focus:ring-2 focus:ring-teal-300"
            type="password"
            minLength={8}
            required
          />
        </label>

        {authError ? (
          <p className="rounded-lg border border-rose-300 bg-rose-50 px-3 py-2 text-sm text-rose-800">{authError}</p>
        ) : null}

        <div className="flex flex-col gap-3 sm:flex-row">
          <Button type="submit" className="flex-1 bg-teal-500 text-stone-950 hover:bg-teal-400" disabled={busy}>
            <LockKeyhole className="h-4 w-4" />
            {busy ? 'Connecting...' : mode === 'login' ? 'Login with API' : 'Create API account'}
          </Button>
          <Button variant="secondary" className="flex-1 border-white/20 bg-white/10 text-white hover:bg-white/20" onClick={onDemo}>
            <PlayCircle className="h-4 w-4" />
            Demo workspace
          </Button>
        </div>
      </form>

      <div className="mt-4 flex items-start gap-2 rounded-lg bg-white/10 p-3 text-sm text-stone-200">
        {apiOnline ? <Wifi className="mt-0.5 h-4 w-4 text-emerald-300" /> : <WifiOff className="mt-0.5 h-4 w-4 text-amber-300" />}
        <p>
          {apiOnline
            ? 'Backend health check is reachable. Login and assessment can use live FastAPI routes.'
            : 'Backend is not reachable yet. Demo mode keeps the presentation running without MongoDB.'}
        </p>
      </div>
    </Panel>
  )
}

const Sidebar = ({ activeView, apiOnline, currentUser, isDemoMode, onLogout, onSetView }) => (
  <aside className="rounded-lg border border-stone-200 bg-white p-4 shadow-sm lg:sticky lg:top-4 lg:h-[calc(100vh-2rem)]">
    <div className="flex items-center gap-3 border-b border-stone-200 pb-4">
      <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-stone-950 text-white">
        <Brain className="h-6 w-6" />
      </div>
      <div>
        <p className="text-lg font-bold text-stone-950">MindBridge</p>
        <p className="text-xs font-medium text-stone-500">Mental wellness journey</p>
      </div>
    </div>

    <div className="mt-4 space-y-2">
      {NAV_ITEMS.map((item) => (
        <button
          key={item.id}
          type="button"
          onClick={() => onSetView(item.id)}
          className={cx(
            'flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm font-semibold transition',
            activeView === item.id ? 'bg-stone-950 text-white' : 'text-stone-600 hover:bg-stone-100 hover:text-stone-950',
          )}
        >
          <item.icon className="h-4 w-4" />
          {item.label}
        </button>
      ))}
    </div>

    <div className="mt-6 space-y-3 rounded-lg bg-stone-50 p-3">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-semibold uppercase tracking-wide text-stone-500">Runtime</span>
        <StatusPill tone={apiOnline ? 'emerald' : 'amber'} icon={apiOnline ? Wifi : WifiOff}>
          {apiOnline ? 'Live API' : 'Demo ready'}
        </StatusPill>
      </div>
      <p className="break-words text-sm font-semibold text-stone-800">{currentUser?.email || 'Guest session'}</p>
      <StatusPill
        tone={isDemoMode ? 'indigo' : currentUser ? 'teal' : 'stone'}
        icon={isDemoMode ? Sparkles : currentUser ? Database : LockKeyhole}
      >
        {isDemoMode ? 'Demo mode' : currentUser ? 'API mode' : 'Guest mode'}
      </StatusPill>
    </div>

    <Button variant="secondary" className="mt-4 w-full" onClick={onLogout}>
      <LogOut className="h-4 w-4" />
      Reset session
    </Button>
  </aside>
)

const OverviewPanel = ({ assessment, history, profile, onSetView }) => {
  const latestResult = assessment.result || history[0]
  const progress = assessment.answers.length

  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Metric label="Backend routes mapped" value="9" icon={Database} tone="teal" />
        <Metric label="Profile fields" value="6" icon={UserRound} tone="indigo" />
        <Metric label="PHQ-9 progress" value={`${progress}/9`} icon={ClipboardCheck} tone="amber" />
        <Metric label="History records" value={String(history.length)} icon={Clock3} tone="rose" />
      </div>

      <Panel
        eyebrow="Submission demo path"
        title="What You are going to see"
        action={
          <Button variant="soft" onClick={() => onSetView('assessment')}>
            Start assessment
            <ArrowRight className="h-4 w-4" />
          </Button>
        }
      >
        <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
          <div className="space-y-3">
            {[
              ['Signup/Login', 'JWT token pair, in-memory frontend session, protected route calls'],
              ['Onboarding', `${profile.age || 'Age'} years, ${profile.occupation || 'occupation'}, sleep and support context`],
              ['Assessment', 'Chat-style PHQ-9 powered by the current LangGraph conversation route'],
              ['Report', 'Insight, coping plan, crisis resources, clinic handoff, follow-up loop'],
            ].map(([title, description], index) => (
              <div key={title} className="flex gap-3 rounded-lg border border-stone-200 bg-stone-50 p-3">
                <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-white text-sm font-bold text-stone-900 ring-1 ring-stone-200">
                  {index + 1}
                </span>
                <div>
                  <p className="font-semibold text-stone-950">{title}</p>
                  <p className="mt-1 text-sm text-stone-600">{description}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="rounded-lg border border-stone-200 bg-white p-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-stone-500">Latest score</p>
                <p className="mt-1 text-3xl font-bold text-stone-950">{latestResult?.total_score ?? '--'}</p>
              </div>
              <StatusPill tone={latestResult?.clinical_risk ? 'rose' : 'emerald'} icon={latestResult?.clinical_risk ? AlertTriangle : ShieldCheck}>
                {latestResult?.clinical_risk ? 'Safety triggered' : formatSeverity(latestResult?.severity)}
              </StatusPill>
            </div>
            <div className="mt-5 h-3 overflow-hidden rounded-full bg-stone-100">
              <div
                className="h-full rounded-full bg-gradient-to-r from-teal-500 via-amber-400 to-rose-500"
                style={{ width: `${Math.min(100, ((latestResult?.total_score || 0) / 27) * 100)}%` }}
              />
            </div>
            <p className="mt-4 text-sm leading-6 text-stone-600">
              {latestResult?.recommendation ||
                'Run the PHQ-9 flow to generate a plain-language result and a handoff-ready wellness plan.'}
            </p>
          </div>
        </div>
      </Panel>

      <ArchitecturePanel />
      <RoadmapPanel />
    </div>
  )
}

const ArchitecturePanel = () => (
  <Panel eyebrow="Architecture" title="Current system map">
    <div className="grid gap-4 xl:grid-cols-[0.85fr_1.15fr]">
      <div className="space-y-3 text-sm leading-6 text-stone-600">
        <p>
          The backend in this repo currently covers auth, profile storage, PHQ-9 scoring, PHQ-9 history, and a
          chat-style conversation route. The frontend mirrors that progress and clearly marks RAG, clinic search, and
          feedback persistence as next-phase work.
        </p>
        <div className="grid gap-2 sm:grid-cols-2">
          <StatusPill tone="emerald" icon={CheckCircle2}>JWT auth</StatusPill>
          <StatusPill tone="emerald" icon={CheckCircle2}>Profile API</StatusPill>
          <StatusPill tone="emerald" icon={CheckCircle2}>PHQ-9 engine</StatusPill>
          <StatusPill tone="amber" icon={Clock3}>RAG next</StatusPill>
        </div>
      </div>
      <div className="overflow-hidden rounded-lg border border-stone-200 bg-black">
        <img
          src="/mindbridge-architecture.png"
          alt="MindBridge system architecture"
          className="h-full max-h-[360px] w-full object-contain"
        />
      </div>
    </div>
  </Panel>
)

const RoadmapPanel = () => (
  <Panel eyebrow="Build status" title="MVP progress snapshot">
    <div className="grid gap-4 lg:grid-cols-3">
      {ROADMAP_ITEMS.map((group) => (
        <div key={group.title} className="rounded-lg border border-stone-200 bg-stone-50 p-4">
          <div className="flex items-center gap-3">
            <span
              className={cx(
                'rounded-lg p-2',
                group.tone === 'emerald' && 'bg-emerald-100 text-emerald-700',
                group.tone === 'indigo' && 'bg-indigo-100 text-indigo-700',
                group.tone === 'amber' && 'bg-amber-100 text-amber-700',
              )}
            >
              <group.icon className="h-4 w-4" />
            </span>
            <p className="font-bold text-stone-950">{group.title}</p>
          </div>
          <div className="mt-4 space-y-2">
            {group.items.map((item) => (
              <div key={item} className="flex gap-2 text-sm text-stone-600">
                <CircleDot className="mt-0.5 h-4 w-4 shrink-0 text-stone-400" />
                <span>{item}</span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  </Panel>
)

const ProfilePanel = ({ busy, isAuthed, onSave, profile }) => {
  const [form, setForm] = useState(profile)
  const [lifeEvents, setLifeEvents] = useState(profile.life_events?.join(', ') || '')

  const updateField = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }))
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    const payload = {
      age: form.age === '' ? null : Number(form.age),
      gender: form.gender || null,
      occupation: form.occupation || null,
      sleep_hours: form.sleep_hours === '' ? null : Number(form.sleep_hours),
      social_support: form.social_support || null,
      life_events: lifeEvents
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean)
        .slice(0, 5),
    }
    onSave(payload)
  }

  return (
    <Panel
      eyebrow="Onboarding"
      title="User profile builder"
      action={<StatusPill tone={isAuthed ? 'emerald' : 'amber'} icon={isAuthed ? ShieldCheck : AlertTriangle}>{isAuthed ? 'Protected route' : 'Login needed'}</StatusPill>}
    >
      <form onSubmit={handleSubmit} className="grid gap-4 lg:grid-cols-2">
        <label className="block">
          <span className="text-sm font-semibold text-stone-700">Age</span>
          <input
            type="number"
            min="10"
            max="100"
            value={form.age ?? ''}
            onChange={(event) => updateField('age', event.target.value)}
            className="mt-2 w-full rounded-lg border border-stone-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-teal-300"
            placeholder="22"
          />
        </label>

        <label className="block">
          <span className="text-sm font-semibold text-stone-700">Gender</span>
          <select
            value={form.gender ?? ''}
            onChange={(event) => updateField('gender', event.target.value)}
            className="mt-2 w-full rounded-lg border border-stone-300 bg-white px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-teal-300"
          >
            <option value="">Prefer not to say</option>
            <option value="male">Male</option>
            <option value="female">Female</option>
            <option value="other">Other</option>
          </select>
        </label>

        <label className="block">
          <span className="text-sm font-semibold text-stone-700">Occupation</span>
          <select
            value={form.occupation ?? ''}
            onChange={(event) => updateField('occupation', event.target.value)}
            className="mt-2 w-full rounded-lg border border-stone-300 bg-white px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-teal-300"
          >
            <option value="">Select one</option>
            <option value="student">Student</option>
            <option value="working">Working</option>
            <option value="unemployed">Unemployed</option>
            <option value="retired">Retired</option>
            <option value="other">Other</option>
          </select>
        </label>

        <label className="block">
          <span className="text-sm font-semibold text-stone-700">Sleep hours</span>
          <input
            type="number"
            min="0"
            max="24"
            value={form.sleep_hours ?? ''}
            onChange={(event) => updateField('sleep_hours', event.target.value)}
            className="mt-2 w-full rounded-lg border border-stone-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-teal-300"
            placeholder="6"
          />
        </label>

        <label className="block">
          <span className="text-sm font-semibold text-stone-700">Social support</span>
          <select
            value={form.social_support ?? ''}
            onChange={(event) => updateField('social_support', event.target.value)}
            className="mt-2 w-full rounded-lg border border-stone-300 bg-white px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-teal-300"
          >
            <option value="">Select one</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </label>

        <label className="block">
          <span className="text-sm font-semibold text-stone-700">Recent life events</span>
          <input
            value={lifeEvents}
            onChange={(event) => setLifeEvents(event.target.value)}
            className="mt-2 w-full rounded-lg border border-stone-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-teal-300"
            placeholder="exams, job change, relocation"
          />
        </label>

        <div className="lg:col-span-2">
          <Button type="submit" disabled={!isAuthed || busy}>
            <UserRound className="h-4 w-4" />
            {busy ? 'Saving...' : 'Save profile'}
          </Button>
        </div>
      </form>
    </Panel>
  )
}

const AssessmentPanel = ({ assessment, isAuthed, isDemoMode, onAnswer, onNotesChange, onReset, onStart }) => {
  const scoreOptions = normalizeScoreOptions(assessment.scoreOptions)
  const progress = Math.round((assessment.answers.length / 9) * 100)

  return (
    <Panel
      eyebrow="Assessment engine"
      title="Chat-style PHQ-9 screener"
      action={
        <div className="flex flex-wrap gap-2">
          <StatusPill tone={isDemoMode ? 'indigo' : 'teal'} icon={isDemoMode ? Sparkles : Database}>
            {isDemoMode ? 'Demo graph' : 'LangGraph route'}
          </StatusPill>
          <Button variant="secondary" onClick={onReset}>
            <RefreshCw className="h-4 w-4" />
            Reset
          </Button>
        </div>
      }
    >
      <div className="grid gap-4 xl:grid-cols-[0.85fr_1.15fr]">
        <div className="space-y-4">
          <label className="block">
            <span className="text-sm font-semibold text-stone-700">Session notes</span>
            <textarea
              value={assessment.notes}
              onChange={(event) => onNotesChange(event.target.value)}
              className="mt-2 min-h-28 w-full rounded-lg border border-stone-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-teal-300"
              placeholder="Optional context saved with the final assessment."
            />
          </label>

          <div className="rounded-lg border border-stone-200 bg-stone-50 p-4">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-semibold text-stone-600">Question progress</p>
              <p className="text-sm font-bold text-stone-950">{assessment.answers.length}/9</p>
            </div>
            <div className="mt-3 h-3 overflow-hidden rounded-full bg-white ring-1 ring-stone-200">
              <div className="h-full rounded-full bg-teal-500 transition-all" style={{ width: `${progress}%` }} />
            </div>
          </div>

          {!assessment.started ? (
            <Button className="w-full" disabled={!isAuthed || assessment.busy} onClick={onStart}>
              <PlayCircle className="h-4 w-4" />
              {assessment.busy ? 'Starting...' : 'Start PHQ-9 conversation'}
            </Button>
          ) : (
            <div className="grid gap-2">
              {scoreOptions.map((option) => (
                <Button
                  key={option.value}
                  variant="secondary"
                  className="justify-between"
                  disabled={!assessment.needsAnswer || assessment.busy || assessment.isComplete}
                  onClick={() => onAnswer(option.value)}
                >
                  <span>{option.label}</span>
                  <span className="rounded-md bg-stone-100 px-2 py-1 text-xs font-bold text-stone-600">{option.value}</span>
                </Button>
              ))}
            </div>
          )}

          {assessment.error ? (
            <p className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-800">{assessment.error}</p>
          ) : null}
        </div>

        <div className="flex min-h-[520px] flex-col rounded-lg border border-stone-200 bg-[#f8faf8]">
          <div className="flex items-center justify-between border-b border-stone-200 px-4 py-3">
            <div className="flex items-center gap-2">
              <HeartPulse className="h-4 w-4 text-teal-700" />
              <p className="text-sm font-bold text-stone-900">MindBridge assessment chat</p>
            </div>
            <StatusPill tone={assessment.isComplete ? 'emerald' : 'amber'} icon={assessment.isComplete ? CheckCircle2 : Activity}>
              {assessment.isComplete ? 'Complete' : 'In progress'}
            </StatusPill>
          </div>

          <div className="flex-1 space-y-3 overflow-y-auto p-4">
            {assessment.messages.length === 0 ? (
              <div className="flex h-full items-center justify-center text-center">
                <div className="max-w-sm">
                  <MessageCircle className="mx-auto h-10 w-10 text-stone-300" />
                  <p className="mt-3 text-sm leading-6 text-stone-500">
                    Start the PHQ-9 conversation to show the real assessment flow: one question, one score, one protected
                    backend call.
                  </p>
                </div>
              </div>
            ) : (
              assessment.messages.map((message) => (
                <div
                  key={message.id}
                  className={cx('flex', message.role === 'user' ? 'justify-end' : 'justify-start')}
                >
                  <div
                    className={cx(
                      'max-w-[82%] rounded-lg px-4 py-3 text-sm leading-6 shadow-sm',
                      message.role === 'user'
                        ? 'bg-stone-950 text-white'
                        : 'border border-stone-200 bg-white text-stone-700',
                    )}
                  >
                    {message.content}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </Panel>
  )
}

const SafetyBanner = ({ crisisSupport }) => {
  if (!crisisSupport) {
    return (
      <Panel className="border-emerald-200 bg-emerald-50" eyebrow="Safety net" title="Crisis support is built into the assessment result">
        <div className="grid gap-3 md:grid-cols-3">
          {['PHQ-9 item 9 flag', 'Helpline surfacing', 'Professional follow-up'].map((item) => (
            <div key={item} className="flex items-center gap-2 rounded-lg bg-white px-3 py-2 text-sm font-semibold text-emerald-800">
              <ShieldCheck className="h-4 w-4" />
              {item}
            </div>
          ))}
        </div>
      </Panel>
    )
  }

  return (
    <Panel className="border-rose-200 bg-rose-50" eyebrow="Crisis safety net" title="Immediate support surfaced">
      <div className="flex gap-3 rounded-lg bg-white p-4 text-rose-900">
        <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" />
        <p className="text-sm leading-6">{crisisSupport.message}</p>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        {(crisisSupport.resources || []).map((resource) => (
          <div key={resource.name} className="rounded-lg border border-rose-200 bg-white p-4">
            <p className="font-bold text-stone-950">{resource.name}</p>
            <p className="mt-2 text-sm font-semibold text-rose-700">{resource.contact}</p>
            <p className="mt-1 text-xs font-medium text-stone-500">{resource.region}</p>
          </div>
        ))}
      </div>
    </Panel>
  )
}

const ReportPanel = ({ assessment, history, profile, onSetView }) => {
  const result = assessment.result || history[0]
  const supportLevel = profile.social_support || 'medium'
  const sleepHours = profile.sleep_hours || 6
  const copingPlan = [
    `Use a 3-minute breathing reset after high-stress moments, especially around ${profile.life_events?.[0] || 'daily routines'}.`,
    `Protect a sleep window near ${sleepHours} hours and repeat the assessment if symptoms increase.`,
    `Plan one check-in with a ${supportLevel} support contact this week.`,
    result?.needs_to_follow
      ? 'Schedule a professional follow-up and bring the score summary to the appointment.'
      : 'Continue self-care habits and repeat the screener during the next check-in.',
  ]

  return (
    <div className="space-y-4">
      <Panel
        eyebrow="Insight report"
        title={result ? 'Generated from the latest PHQ-9 result' : 'Report preview'}
        action={
          <Button variant="soft" onClick={() => onSetView('clinics')}>
            Clinic handoff
            <MapPin className="h-4 w-4" />
          </Button>
        }
      >
        <div className="grid gap-4 xl:grid-cols-[0.75fr_1.25fr]">
          <div className="rounded-lg border border-stone-200 bg-stone-50 p-5">
            <p className="text-sm font-semibold text-stone-500">PHQ-9 score</p>
            <p className="mt-2 text-5xl font-bold text-stone-950">{result?.total_score ?? '--'}</p>
            <StatusPill tone={result?.clinical_risk ? 'rose' : 'amber'} icon={result?.clinical_risk ? AlertTriangle : ClipboardCheck}>
              {formatSeverity(result?.severity)}
            </StatusPill>
            <div className="mt-5 h-3 overflow-hidden rounded-full bg-white ring-1 ring-stone-200">
              <div
                className="h-full rounded-full bg-gradient-to-r from-teal-500 via-amber-400 to-rose-500"
                style={{ width: `${Math.min(100, ((result?.total_score || 0) / 27) * 100)}%` }}
              />
            </div>
          </div>
          <div className="space-y-4">
            <div className="rounded-lg border border-stone-200 bg-white p-4">
              <p className="font-bold text-stone-950">Plain-language insight</p>
              <p className="mt-2 text-sm leading-6 text-stone-600">
                {result?.recommendation ||
                  'Complete the PHQ-9 conversation to generate a result. This app is a screening and wellness support tool, not a diagnosis.'}
              </p>
            </div>
            <div className="rounded-lg border border-stone-200 bg-white p-4">
              <p className="font-bold text-stone-950">Personalized coping plan</p>
              <div className="mt-3 grid gap-2">
                {copingPlan.map((item) => (
                  <div key={item} className="flex gap-2 text-sm leading-6 text-stone-600">
                    <CheckCircle2 className="mt-1 h-4 w-4 shrink-0 text-teal-600" />
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </Panel>

      <SafetyBanner crisisSupport={result?.crisis_support || assessment.crisisSupport} />
    </div>
  )
}

const ClinicFinderPanel = () => (
  <Panel
    eyebrow="Clinic finder"
    title="Professional referral cards"
    action={<StatusPill tone="amber" icon={MapPin}>Static demo until Google Maps API</StatusPill>}
  >
    <div className="mb-4 flex flex-col gap-3 rounded-lg border border-stone-200 bg-stone-50 p-4 md:flex-row md:items-center md:justify-between">
      <div>
        <p className="font-bold text-stone-950">Bengaluru demo location</p>
        <p className="mt-1 text-sm text-stone-600">This mirrors the future Google Maps Places API output shape.</p>
      </div>
      <Button variant="secondary">
        <MapPin className="h-4 w-4" />
        Use browser location
      </Button>
    </div>

    <div className="grid gap-4 lg:grid-cols-3">
      {DEMO_CLINICS.map((clinic) => (
        <div key={clinic.name} className="rounded-lg border border-stone-200 bg-white p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="font-bold text-stone-950">{clinic.name}</p>
              <p className="mt-1 text-sm text-stone-500">{clinic.type}</p>
            </div>
            <span className="inline-flex items-center gap-1 rounded-lg bg-amber-50 px-2 py-1 text-xs font-bold text-amber-700">
              <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />
              {clinic.rating}
            </span>
          </div>
          <div className="mt-4 space-y-2 text-sm text-stone-600">
            <p className="flex gap-2">
              <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-teal-700" />
              {clinic.address} - {clinic.distance}
            </p>
            <p className="flex gap-2">
              <Clock3 className="mt-0.5 h-4 w-4 shrink-0 text-indigo-700" />
              Next slot: {clinic.nextSlot}
            </p>
          </div>
          <Button variant="soft" className="mt-4 w-full">
            <Stethoscope className="h-4 w-4" />
            Prepare referral card
          </Button>
        </div>
      ))}
    </div>
  </Panel>
)

const FeedbackPanel = () => {
  const [rating, setRating] = useState(4)
  const [comment, setComment] = useState('')
  const [saved, setSaved] = useState(false)

  const handleSubmit = (event) => {
    event.preventDefault()
    setSaved(true)
  }

  return (
    <Panel eyebrow="Longitudinal loop" title="Feedback and follow-up check-ins">
      <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border border-stone-200 bg-stone-50 p-4">
          <div>
            <p className="text-sm font-semibold text-stone-700">Session rating</p>
            <div className="mt-2 grid grid-cols-5 gap-2">
              {[1, 2, 3, 4, 5].map((value) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setRating(value)}
                  className={cx(
                    'rounded-lg border px-3 py-2 text-sm font-bold transition',
                    rating === value
                      ? 'border-stone-950 bg-stone-950 text-white'
                      : 'border-stone-300 bg-white text-stone-700 hover:bg-stone-100',
                  )}
                >
                  {value}
                </button>
              ))}
            </div>
          </div>
          <label className="block">
            <span className="text-sm font-semibold text-stone-700">Open feedback</span>
            <textarea
              value={comment}
              onChange={(event) => setComment(event.target.value)}
              className="mt-2 min-h-28 w-full rounded-lg border border-stone-300 bg-white px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-teal-300"
              placeholder="What felt useful, confusing, or missing?"
            />
          </label>
          <Button type="submit">
            <Send className="h-4 w-4" />
            Save feedback
          </Button>
          {saved ? <p className="text-sm font-semibold text-emerald-700">Feedback captured for the demo flow.</p> : null}
        </form>

        <div className="grid gap-3">
          {[
            ['Day 0', 'Assessment complete', 'PHQ-9 result and report generated'],
            ['Day 7', 'Check-in prompt', 'Repeat screener and compare symptom trend'],
            ['Day 30', 'Outcome tracking', 'Longitudinal data for future model improvement'],
          ].map(([day, title, description]) => (
            <div key={day} className="flex gap-3 rounded-lg border border-stone-200 bg-white p-4">
              <span className="flex h-10 w-14 shrink-0 items-center justify-center rounded-lg bg-indigo-50 text-sm font-bold text-indigo-700">
                {day}
              </span>
              <div>
                <p className="font-bold text-stone-950">{title}</p>
                <p className="mt-1 text-sm leading-6 text-stone-600">{description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Panel>
  )
}

function App() {
  const [activeView, setActiveView] = useState('overview')
  const [apiOnline, setApiOnline] = useState(false)
  const [authMode, setAuthMode] = useState('guest')
  const [tokens, setTokens] = useState(null)
  const [currentUser, setCurrentUser] = useState(null)
  const [profile, setProfile] = useState(DEFAULT_PROFILE)
  const [history, setHistory] = useState([])
  const [assessment, setAssessment] = useState(emptyAssessment)
  const [authError, setAuthError] = useState('')
  const [busy, setBusy] = useState(false)
  const [profileBusy, setProfileBusy] = useState(false)

  const isDemoMode = authMode === 'demo'
  const isAuthed = Boolean(tokens?.access_token)

  useEffect(() => {
    let active = true

    api
      .health()
      .then(() => {
        if (active) setApiOnline(true)
      })
      .catch(() => {
        if (active) setApiOnline(false)
      })

    return () => {
      active = false
    }
  }, [])

  const statusCopy = useMemo(() => {
    if (isDemoMode) return 'Demo mode is active, so every screen is available without a backend.'
    if (isAuthed) return 'Live API session is active. Protected routes will use the access token in memory.'
    return 'Login to use live protected routes, or start the demo workspace for presentation mode.'
  }, [isAuthed, isDemoMode])

  const hydrateProtectedData = async (accessToken) => {
    const [profileResult, historyResult] = await Promise.allSettled([
      api.getProfile(accessToken),
      api.getPhq9History(accessToken),
    ])

    if (profileResult.status === 'fulfilled' && profileResult.value) {
      setProfile({
        ...DEFAULT_PROFILE,
        ...profileResult.value,
        age: profileResult.value.age ?? '',
        sleep_hours: profileResult.value.sleep_hours ?? '',
      })
    }

    if (historyResult.status === 'fulfilled') {
      setHistory(historyResult.value?.items || [])
    }
  }

  const handleAuth = async (mode, credentials) => {
    setBusy(true)
    setAuthError('')

    try {
      const tokenResponse = mode === 'register' ? await api.register(credentials) : await api.login(credentials)
      setTokens(tokenResponse)
      setAuthMode('api')
      const me = await api.me(tokenResponse.access_token)
      setCurrentUser(me)
      await hydrateProtectedData(tokenResponse.access_token)
      setActiveView('overview')
    } catch (error) {
      setAuthError(error.message || 'Could not connect to the backend. Use demo mode for the presentation.')
    } finally {
      setBusy(false)
    }
  }

  const handleDemo = () => {
    setAuthMode('demo')
    setTokens({ access_token: 'demo-access-token', refresh_token: 'demo-refresh-token', token_type: 'bearer' })
    setCurrentUser({ email: 'demo@mindbridge.app' })
    setProfile(DEMO_PROFILE)
    setHistory([])
    setAssessment(emptyAssessment)
    setAuthError('')
    setActiveView('overview')
  }

  const handleLogout = async () => {
    if (tokens?.access_token && !isDemoMode) {
      try {
        await api.logout(tokens.access_token)
      } catch {
        setApiOnline(false)
      }
    }

    setAuthMode('guest')
    setTokens(null)
    setCurrentUser(null)
    setProfile(DEFAULT_PROFILE)
    setHistory([])
    setAssessment(emptyAssessment)
    setActiveView('overview')
  }

  const handleSaveProfile = async (payload) => {
    setProfileBusy(true)

    try {
      if (isDemoMode) {
        setProfile(payload)
      } else {
        const updated = await api.updateProfile(tokens.access_token, payload)
        setProfile({ ...updated, age: updated.age ?? '', sleep_hours: updated.sleep_hours ?? '' })
      }
    } catch (error) {
      setAssessment((current) => ({ ...current, error: error.message || 'Profile save failed.' }))
    } finally {
      setProfileBusy(false)
    }
  }

  const updateAssessmentFromResponse = (response, existingMessages = []) => {
    const assistantMessage = {
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: response.assistant_message,
    }

    setAssessment((current) => ({
      ...current,
      started: true,
      answers: response.answers || [],
      messages: [...existingMessages, assistantMessage],
      currentQuestionId: response.current_question_id,
      scoreOptions: response.score_options || SCORE_OPTIONS,
      isComplete: response.is_complete,
      needsAnswer: response.needs_answer,
      result: response.result,
      crisisSupport: response.crisis_support,
      busy: false,
      error: response.error || '',
    }))

    if (response.result) {
      setHistory((items) => [toHistoryItem(response.result, assessment.notes), ...items].slice(0, 5))
      setActiveView('report')
    }
  }

  const handleStartAssessment = async () => {
    setAssessment((current) => ({ ...current, busy: true, error: '' }))

    try {
      const response = isDemoMode
        ? buildDemoStart()
        : await api.startPhq9(tokens.access_token, { notes: assessment.notes || undefined })
      updateAssessmentFromResponse(response, [])
    } catch (error) {
      setAssessment((current) => ({
        ...current,
        busy: false,
        error: error.message || 'Could not start the PHQ-9 conversation.',
      }))
    }
  }

  const handleAnswer = async (score) => {
    const userMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: SCORE_OPTIONS[score],
    }
    const nextMessages = [...assessment.messages, userMessage]

    setAssessment((current) => ({ ...current, messages: nextMessages, busy: true, error: '' }))

    try {
      const response = isDemoMode
        ? continueDemoConversation(assessment.answers, score)
        : await api.answerPhq9(tokens.access_token, {
            answers: assessment.answers,
            score,
            notes: assessment.notes || undefined,
          })
      updateAssessmentFromResponse(response, nextMessages)
    } catch (error) {
      setAssessment((current) => ({
        ...current,
        busy: false,
        error: error.message || 'Could not submit that assessment answer.',
      }))
    }
  }

  const handleAssessmentNotesChange = (notes) => {
    setAssessment((current) => ({ ...current, notes }))
  }

  const handleResetAssessment = () => {
    setAssessment((current) => ({ ...emptyAssessment, notes: current.notes }))
  }

  const renderActiveView = () => {
    if (activeView === 'profile') {
      return <ProfilePanel busy={profileBusy} isAuthed={isAuthed} onSave={handleSaveProfile} profile={profile} />
    }

    if (activeView === 'assessment') {
      return (
        <AssessmentPanel
          assessment={assessment}
          isAuthed={isAuthed}
          isDemoMode={isDemoMode}
          onAnswer={handleAnswer}
          onNotesChange={handleAssessmentNotesChange}
          onReset={handleResetAssessment}
          onStart={handleStartAssessment}
        />
      )
    }

    if (activeView === 'report') {
      return <ReportPanel assessment={assessment} history={history} profile={profile} onSetView={setActiveView} />
    }

    if (activeView === 'clinics') {
      return <ClinicFinderPanel />
    }

    if (activeView === 'feedback') {
      return <FeedbackPanel />
    }

    return <OverviewPanel assessment={assessment} history={history} profile={profile} onSetView={setActiveView} />
  }

  return (
    <div className="fixed inset-0 overflow-y-auto bg-[#f6f2e8] text-stone-950">
      <div className="mx-auto grid min-h-full w-full max-w-[1500px] gap-4 px-4 py-4 lg:grid-cols-[280px_1fr]">
        <Sidebar
          activeView={activeView}
          apiOnline={apiOnline}
          currentUser={currentUser}
          isDemoMode={isDemoMode}
          onLogout={handleLogout}
          onSetView={setActiveView}
        />

        <main className="space-y-4">
          <div className="rounded-lg border border-stone-200 bg-white p-5 shadow-sm">
            <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
              <div>
                <div className="flex flex-wrap gap-2">
                  <StatusPill tone={apiOnline ? 'emerald' : 'amber'} icon={apiOnline ? Wifi : WifiOff}>
                    {apiOnline ? 'FastAPI reachable' : 'Backend offline'}
                  </StatusPill>
                  <StatusPill tone={isAuthed ? 'teal' : 'stone'} icon={isAuthed ? ShieldCheck : LockKeyhole}>
                    {isAuthed ? 'Session ready' : 'Guest'}
                  </StatusPill>
                </div>
                <h1 className="mt-3 text-2xl font-black tracking-normal text-stone-950 sm:text-3xl">
                  MindBridge frontend demo workspace
                </h1>
                <p className="mt-2 max-w-3xl text-sm leading-6 text-stone-600">{statusCopy}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button variant="secondary" onClick={() => setActiveView('profile')}>
                  <UserRound className="h-4 w-4" />
                  Profile
                </Button>
                <Button onClick={() => setActiveView('assessment')}>
                  <Brain className="h-4 w-4" />
                  PHQ-9 flow
                </Button>
              </div>
            </div>
          </div>

          {!isAuthed ? (
            <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
              <AuthPanel apiOnline={apiOnline} authError={authError} busy={busy} onDemo={handleDemo} onSubmit={handleAuth} />
              <ArchitecturePanel />
            </div>
          ) : (
            renderActiveView()
          )}
        </main>
      </div>
    </div>
  )
}

export default App
