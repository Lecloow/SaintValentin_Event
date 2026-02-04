import{S as i}from"./storage-BBbnFWtQ.js";class n{constructor(){this.contentEl=null,this.init()}init(){this.contentEl=document.getElementById("content"),this.render()}render(){if(!this.contentEl)return;const e=i.getUser();if(!e){this.renderNotConnected();return}this.renderProfile(e)}renderNotConnected(){this.contentEl&&(this.contentEl.innerHTML=`
      <div class="error">Vous n'êtes pas connecté. Redirection...</div>
    `,setTimeout(()=>{window.location.href="./index.html"},2e3))}renderProfile(e){this.contentEl&&(this.contentEl.innerHTML=`
      <div class="greeting">Bonjour ${e.first_name}! 👋</div>
      
      <div class="user-info">
        <div class="info-row">
          <div class="label">Prénom</div>
          <div class="value">${e.first_name}</div>
        </div>
        <div class="info-row">
          <div class="label">Nom</div>
          <div class="value">${e.last_name}</div>
        </div>
        <div class="info-row">
          <div class="label">Email</div>
          <div class="value">${e.email}</div>
        </div>
        <div class="info-row">
          <div class="label">Classe</div>
          <div class="value">${e.currentClass}</div>
        </div>
      </div>

      <button class="logout-btn" onclick="logout()">Se déconnecter</button>
    `)}}window.logout=function(){i.clearUser(),window.location.href="./index.html"};document.addEventListener("DOMContentLoaded",()=>{new n});
