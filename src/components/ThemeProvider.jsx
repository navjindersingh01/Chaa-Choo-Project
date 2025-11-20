import React, { createContext, useContext, useEffect, useState } from 'react'

const ThemeContext = createContext()

export function ThemeProvider({ children }){
  const [theme, setTheme] = useState('light')

  useEffect(()=>{
    // Hydrate from localStorage, SSR-safe pattern
    try{
      const saved = window.localStorage.getItem('chaa-choo-theme')
      if (saved) setTheme(saved)
      // apply to document root
      document.documentElement.setAttribute('data-theme', saved || 'light')
    }catch(e){
      // ignore in SSR or restricted env
    }
  }, [])

  useEffect(()=>{
    try{
      window.localStorage.setItem('chaa-choo-theme', theme)
      document.documentElement.setAttribute('data-theme', theme)
    }catch(e){}
  }, [theme])

  const toggle = () => setTheme(t => t === 'light' ? 'dark' : 'light')

  return (
    <ThemeContext.Provider value={{theme, setTheme, toggle}}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme(){
  return useContext(ThemeContext)
}

export function ThemeToggle(){
  const { theme, toggle } = useTheme()
  return (
    <button onClick={toggle} aria-label="Toggle theme" className="px-3 py-1 rounded focus-ring" style={{background:'var(--color-primary)',color:'#fff'}}>
      {theme === 'light' ? '🌞 Light' : '🌙 Dark'}
    </button>
  )
}

export default ThemeProvider
