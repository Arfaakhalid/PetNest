// Main UI interactions for PetNest demo
document.addEventListener('DOMContentLoaded', function(){
  // mobile nav
  const navToggle = document.getElementById('navToggle');
  const navMenu = document.querySelector('.nav-menu');
  if(navToggle) navToggle.addEventListener('click', ()=> navMenu.classList.toggle('active'));

  // theme
  const themeToggle = document.getElementById('themeToggle');
  const body = document.body;
  const currentTheme = localStorage.getItem('theme') || 'light';
  if(currentTheme === 'dark') body.classList.add('dark-mode');
  if(themeToggle) themeToggle.addEventListener('click', ()=>{
    body.classList.toggle('dark-mode');
    const isDark = body.classList.contains('dark-mode');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
  });

  // populate home categories quickly if present
  const homeGrid = document.getElementById('homeCategoryGrid');
  if(homeGrid){
    const cats = ['Dogs','Cats','Birds','Fish','Goats','Hens','Rabbits','Other'];
    cats.forEach(c=>{
      const div = document.createElement('div'); div.className='category-card';
      div.innerHTML = `<img src="https://source.unsplash.com/collection/190727/600x400?${c}"><h3>${c}</h3><p>Explore magical ${c.toLowerCase()} listings</p><a class="btn btn-outline" href="adopt.html">Discover</a>`;
      homeGrid.appendChild(div);
    });
    // add tilt
    if(window.VanillaTilt) VanillaTilt.init(document.querySelectorAll('[data-tilt], .category-card'), {max:12, speed:400, glare:true, "max-glare":0.2});
  }

  // modal openers
  document.querySelectorAll('#openLogin').forEach(b=>b.addEventListener('click', e=>{ e.preventDefault(); document.getElementById('loginModal').classList.add('active'); }));
  document.querySelectorAll('#openSignup').forEach(b=>b.addEventListener('click', e=>{ e.preventDefault(); alert('Please use the Sign Up page (demo).'); }));

  document.querySelectorAll('.close-modal').forEach(btn=>btn.addEventListener('click', ()=>{ document.querySelectorAll('.modal').forEach(m=>m.classList.remove('active')); }));

});
