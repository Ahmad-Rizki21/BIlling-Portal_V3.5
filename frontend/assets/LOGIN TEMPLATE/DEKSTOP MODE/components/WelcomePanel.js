function WelcomePanel() {
  try {
    return (
      <div className="hidden lg:flex lg:w-[55%] blue-gradient-bg relative overflow-hidden items-center justify-center" data-name="welcome-panel" data-file="components/WelcomePanel.js">
        <div className="absolute inset-0">
          <div className="absolute -top-32 -right-32 w-[400px] h-[400px] bg-blue-400 rounded-full opacity-30 blur-3xl"></div>
          <div className="absolute top-20 right-20 w-[350px] h-[350px] bg-blue-500 rounded-full opacity-25 blur-3xl"></div>
          <div className="absolute -bottom-40 -right-40 w-[500px] h-[500px] bg-blue-600 rounded-full opacity-30 blur-3xl"></div>
          <div className="absolute bottom-32 right-10 w-[380px] h-[380px] bg-blue-400 rounded-full opacity-20 blur-3xl"></div>
        </div>

        <div className="relative z-10 text-center text-white px-12">
          <h1 className="text-5xl font-bold mb-5 tracking-wide">WOELCOME!</h1>
          <p className="text-base opacity-90 max-w-sm mx-auto leading-relaxed">
            Enter your details and start our journy with us
          </p>
        </div>
      </div>
    );
  } catch (error) {
    console.error('WelcomePanel component error:', error);
    return null;
  }
}
