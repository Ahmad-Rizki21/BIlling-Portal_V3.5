function LoginForm({ onLogin }) {
  try {
    const [email, setEmail] = React.useState('');
    const [password, setPassword] = React.useState('');
    const [remember, setRemember] = React.useState(false);

    const handleSubmit = (e) => {
      e.preventDefault();
      if (email && password) {
        onLogin(email, password, remember);
      }
    };

    return (
      <div className="w-full lg:w-[45%] glass-effect px-8 md:px-12 py-16 flex items-center" data-name="login-form" data-file="components/LoginForm.js">
        <div className="w-full max-w-sm mx-auto">
          <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-8 pb-1 border-b-2 border-gray-300 inline-block">Login please</h2>
          
          <form onSubmit={handleSubmit} className="mt-10">
            <div className="mb-5">
              <div className="flex items-center input-border bg-white rounded px-3 py-2.5 shadow-sm">
                <div className="icon-mail text-base text-gray-400 mr-3"></div>
                <input
                  type="text"
                  placeholder="Input your user name or Email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="flex-1 outline-none text-gray-700 bg-transparent placeholder-gray-400 text-sm"
                />
              </div>
            </div>

            <div className="mb-3">
              <div className="flex items-center input-border bg-white rounded px-3 py-2.5 shadow-sm">
                <div className="icon-key text-base text-gray-400 mr-3"></div>
                <input
                  type="password"
                  placeholder="Input your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="flex-1 outline-none text-gray-700 bg-transparent placeholder-gray-400 text-sm"
                />
              </div>
            </div>

            <div className="flex items-center justify-end mb-1">
              <a href="#" className="text-xs text-[var(--text-secondary)] hover:text-[var(--primary-color)] transition-colors">
                Forget password?
              </a>
            </div>

            <div className="flex items-center mb-6">
              <input
                type="checkbox"
                checked={remember}
                onChange={(e) => setRemember(e.target.checked)}
                className="w-4 h-4 accent-[var(--primary-color)] cursor-pointer"
                id="remember"
              />
              <label htmlFor="remember" className="ml-2 text-sm text-[var(--text-secondary)] cursor-pointer">
                Remember me
              </label>
            </div>

            <button
              type="submit"
              className="w-full btn-primary text-white py-3 rounded font-medium hover:opacity-90 transition-all flex items-center justify-center"
            >
              <div className="icon-log-in text-base mr-2"></div>
              LOG IN
            </button>
          </form>
        </div>
      </div>
    );
  } catch (error) {
    console.error('LoginForm component error:', error);
    return null;
  }
}
