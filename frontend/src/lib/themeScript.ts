const KEY = "theme";

// <head> ichida chiziladigan skript: sahifa chizilishidan oldin to‘g‘ri mavzu (miltillashsiz)
export const themeInitScript = `(function(){try{var c=localStorage.getItem('${KEY}')||'system';var d=c==='dark'||(c==='system'&&matchMedia('(prefers-color-scheme: dark)').matches);var r=document.documentElement;r.classList.toggle('dark',d);r.style.colorScheme=d?'dark':'light'}catch(e){}})();`;

