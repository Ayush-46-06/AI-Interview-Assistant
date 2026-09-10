import { useEffect, useState } from 'react'
import AppLayout from '../components/AppLayout'
import { useProfileStore } from '../store/profileStore'
import { UploadCloud, CheckCircle, FileText, AlertCircle } from 'lucide-react'

export default function ContextPage(): React.JSX.Element {
  const {
    profile,
    isLoading,
    isSaving,
    isUploading,
    error,
    uploadError,
    fetchProfile,
    saveProfileContext,
    uploadResumeFile,
    clearErrors
  } = useProfileStore()

  // Local form state
  const [targetRole, setTargetRole] = useState('')
  const [technologies, setTechnologies] = useState('')
  const [jdText, setJdText] = useState('')
  const [resumeText, setResumeText] = useState('')
  
  // Preferences
  const [experienceYears, setExperienceYears] = useState<string>('')
  const [currentCompany, setCurrentCompany] = useState('')
  const [keyAchievements, setKeyAchievements] = useState('')
  const [companyInfo, setCompanyInfo] = useState('')
  const [behavioralContext, setBehavioralContext] = useState('')
  const [pastProjects, setPastProjects] = useState('')

  const [saveSuccess, setSaveSuccess] = useState(false)
  const [uploadSuccess, setUploadSuccess] = useState(false)

  // Initialize form when profile loads
  useEffect(() => {
    fetchProfile()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (profile) {
      setTargetRole(profile.target_role || '')
      setTechnologies(profile.technologies?.join(', ') || '')
      setJdText(profile.jd_text || '')
      setResumeText(profile.resume_text || '')
      
      const prefs = profile.preferences || {}
      setExperienceYears(prefs.experience_years?.toString() || '')
      setCurrentCompany((prefs.current_company as string) || '')
      setKeyAchievements((prefs.key_achievements as string[])?.join('\n') || '')
      setCompanyInfo((prefs.company_info as string) || '')
      setBehavioralContext((prefs.behavioral_context as string) || '')
      setPastProjects((prefs.past_projects as string[])?.join('\n') || '')
    }
  }, [profile])

  async function handleSaveContext(e?: React.FormEvent) {
    if (e) e.preventDefault()
    clearErrors()
    setSaveSuccess(false)

    // Parse array fields
    const techArray = technologies.split(',').map((t) => t.trim()).filter(Boolean)
    const achievementsArray = keyAchievements.split('\n').map((a) => a.trim()).filter(Boolean)
    const projectsArray = pastProjects.split('\n').map((p) => p.trim()).filter(Boolean)
    const exp = parseInt(experienceYears, 10)

    const success = await saveProfileContext({
      target_role: targetRole || null,
      technologies: techArray.length > 0 ? techArray : null,
      jd_text: jdText || null,
      resume_text: resumeText || null, // Ensure editable resume_text is sent
      preferences: {
        experience_years: isNaN(exp) ? null : exp,
        current_company: currentCompany || null,
        key_achievements: achievementsArray.length > 0 ? achievementsArray : null,
        company_info: companyInfo || null,
        behavioral_context: behavioralContext || null,
        past_projects: projectsArray.length > 0 ? projectsArray : null
      }
    })

    if (success) {
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 3000)
    }
  }

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return

    // Client-side validation
    if (file.size > 5 * 1024 * 1024) {
      alert('File exceeds 5MB limit.')
      e.target.value = ''
      return
    }

    clearErrors()
    setUploadSuccess(false)
    const success = await uploadResumeFile(file)
    if (success) {
      setUploadSuccess(true)
      setTimeout(() => setUploadSuccess(false), 5000)
    }
    e.target.value = '' // reset input
  }

  if (isLoading && !profile) {
    return (
      <AppLayout>
        <div className="flex h-full items-center justify-center text-gray-500">
          Loading context...
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <div className="p-8 max-w-4xl mx-auto space-y-8 pb-32">
        <div>
          <h1 className="text-2xl font-semibold text-white">Interview Context Manager</h1>
          <p className="text-gray-400 text-sm mt-1">
            Configure the background information the AI uses to customize your interviews.
          </p>
        </div>

        {error && (
          <div className="bg-red-900/30 border border-red-700 text-red-300 p-4 rounded text-sm flex items-start gap-2">
            <AlertCircle size={18} className="mt-0.5 shrink-0" />
            <p>{error}</p>
          </div>
        )}

        {/* Section: Target Interview */}
        <section className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
          <div className="bg-gray-800/50 px-6 py-4 border-b border-gray-800">
            <h2 className="text-lg font-medium text-white">Target Interview</h2>
          </div>
          <div className="p-6 space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Target Role</label>
              <input
                type="text"
                value={targetRole}
                onChange={(e) => setTargetRole(e.target.value)}
                placeholder="e.g. Senior Frontend Engineer"
                maxLength={100}
                className="w-full bg-gray-800 border border-gray-700 text-white px-4 py-2.5 rounded focus:outline-none focus:border-blue-500 transition-colors text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Technologies (comma separated)</label>
              <input
                type="text"
                value={technologies}
                onChange={(e) => setTechnologies(e.target.value)}
                placeholder="e.g. React, TypeScript, Node.js"
                className="w-full bg-gray-800 border border-gray-700 text-white px-4 py-2.5 rounded focus:outline-none focus:border-blue-500 transition-colors text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Job Description</label>
              <textarea
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
                placeholder="Paste the full job description here..."
                maxLength={50000}
                className="w-full h-40 bg-gray-800 border border-gray-700 text-white px-4 py-3 rounded focus:outline-none focus:border-blue-500 transition-colors text-sm resize-y"
              />
            </div>
          </div>
        </section>

        {/* Section: Resume */}
        <section className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
          <div className="bg-gray-800/50 px-6 py-4 border-b border-gray-800">
            <h2 className="text-lg font-medium text-white">Resume Context</h2>
          </div>
          <div className="p-6 space-y-6">
            {/* Upload Area */}
            <div className="bg-gray-800/50 border border-dashed border-gray-700 rounded-lg p-6 text-center">
              <UploadCloud className="mx-auto text-gray-400 mb-3" size={32} />
              <p className="text-sm text-gray-300 mb-2">Upload your resume to automatically extract context</p>
              <p className="text-xs text-gray-500 mb-4">Supported formats: PDF, DOCX (Max 5MB)</p>
              
              <label className="cursor-pointer inline-flex items-center justify-center bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded text-sm font-medium transition-colors">
                {isUploading ? 'Uploading & Parsing...' : 'Select File'}
                <input
                  type="file"
                  accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                  className="hidden"
                  onChange={handleFileUpload}
                  disabled={isUploading}
                />
              </label>

              {uploadError && <p className="text-red-400 text-xs mt-3">{uploadError}</p>}
              {uploadSuccess && <p className="text-green-400 text-xs mt-3 flex items-center justify-center gap-1"><CheckCircle size={14}/> Extracted successfully!</p>}
            </div>

            {/* Extracted Text */}
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
                <FileText size={16} /> Extracted Resume Text
              </label>
              <textarea
                value={resumeText}
                onChange={(e) => setResumeText(e.target.value)}
                placeholder="Extracted resume text will appear here. You can manually edit it to ensure the AI gets the best context."
                maxLength={50000}
                className="w-full h-48 bg-gray-800 border border-gray-700 text-gray-300 px-4 py-3 rounded focus:outline-none focus:border-blue-500 transition-colors text-sm resize-y font-mono"
              />
            </div>
          </div>
        </section>

        {/* Section: Additional Profile Info */}
        <section className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
          <div className="bg-gray-800/50 px-6 py-4 border-b border-gray-800">
            <h2 className="text-lg font-medium text-white">Experience & Background</h2>
          </div>
          <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Years of Experience</label>
              <input
                type="number"
                min="0"
                max="100"
                value={experienceYears}
                onChange={(e) => setExperienceYears(e.target.value)}
                placeholder="e.g. 5"
                className="w-full bg-gray-800 border border-gray-700 text-white px-4 py-2.5 rounded focus:outline-none focus:border-blue-500 transition-colors text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Current Company/Role</label>
              <input
                type="text"
                value={currentCompany}
                onChange={(e) => setCurrentCompany(e.target.value)}
                placeholder="e.g. Software Engineer at Google"
                maxLength={200}
                className="w-full bg-gray-800 border border-gray-700 text-white px-4 py-2.5 rounded focus:outline-none focus:border-blue-500 transition-colors text-sm"
              />
            </div>
            
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-300 mb-2">Key Achievements (One per line)</label>
              <textarea
                value={keyAchievements}
                onChange={(e) => setKeyAchievements(e.target.value)}
                placeholder="Led migration to React, improving load times by 40%&#10;Mentored 3 junior developers"
                className="w-full h-24 bg-gray-800 border border-gray-700 text-white px-4 py-3 rounded focus:outline-none focus:border-blue-500 transition-colors text-sm resize-y"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-300 mb-2">Past Projects (One per line)</label>
              <textarea
                value={pastProjects}
                onChange={(e) => setPastProjects(e.target.value)}
                placeholder="E-commerce redesign&#10;Authentication microservice"
                className="w-full h-24 bg-gray-800 border border-gray-700 text-white px-4 py-3 rounded focus:outline-none focus:border-blue-500 transition-colors text-sm resize-y"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-300 mb-2">Behavioral Context (Optional)</label>
              <textarea
                value={behavioralContext}
                onChange={(e) => setBehavioralContext(e.target.value)}
                placeholder="I want to emphasize my leadership in resolving conflicts and working across functional teams..."
                className="w-full h-24 bg-gray-800 border border-gray-700 text-white px-4 py-3 rounded focus:outline-none focus:border-blue-500 transition-colors text-sm resize-y"
              />
            </div>
            
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-300 mb-2">Company Research / Info (Optional)</label>
              <textarea
                value={companyInfo}
                onChange={(e) => setCompanyInfo(e.target.value)}
                placeholder="Any notes about the target company's values, recent news, or tech stack..."
                className="w-full h-24 bg-gray-800 border border-gray-700 text-white px-4 py-3 rounded focus:outline-none focus:border-blue-500 transition-colors text-sm resize-y"
              />
            </div>
          </div>
        </section>

        {/* Floating Action Bar */}
        <div className="fixed bottom-0 left-52 right-0 p-4 bg-gray-900 border-t border-gray-800 flex justify-end items-center gap-4 z-10 shadow-lg">
          {saveSuccess && (
            <span className="text-green-400 text-sm flex items-center gap-1">
              <CheckCircle size={16} /> Context saved successfully
            </span>
          )}
          <button
            onClick={handleSaveContext}
            disabled={isSaving || isUploading}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-8 py-2.5 rounded font-medium transition-colors shadow-sm"
          >
            {isSaving ? 'Saving...' : 'Save Context'}
          </button>
        </div>
      </div>
    </AppLayout>
  )
}
