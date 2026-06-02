function toggleNotifs(){
  const d=document.getElementById('notifDropdown');
  d.classList.toggle('open');
}
document.addEventListener('click',function(e){
  const btn=document.getElementById('notifBtn');
  const drop=document.getElementById('notifDropdown');
  if(drop&&btn&&!btn.contains(e.target)&&!drop.contains(e.target)){
    drop.classList.remove('open');
  }
});
function markAllRead(){
  fetch('/notifications/read',{method:'POST'}).then(()=>{
    document.querySelectorAll('.notif-item.unread').forEach(el=>el.classList.remove('unread'));
    const b=document.querySelector('.notif-badge');
    if(b)b.remove();
  });
}
function filterTable(){
  const search=(document.getElementById('searchInput')?.value||'').toLowerCase();
  const status=(document.getElementById('statusFilter')?.value||'').toLowerCase();
  document.querySelectorAll('#vehicleTable tbody tr').forEach(row=>{
    const text=row.textContent.toLowerCase();
    row.style.display=(!search||text.includes(search))&&(!status||text.includes(status))?'':'none';
  });
}
document.querySelectorAll('.alert').forEach(el=>{
  setTimeout(()=>{el.style.opacity='0';setTimeout(()=>el.remove(),400);},4000);
  el.style.transition='opacity 0.4s';
});
document.querySelectorAll('form').forEach(form=>{
  if(form.querySelector('.btn-danger')){
    form.addEventListener('submit',function(e){
      if(!confirm('Reject this vehicle registration?'))e.preventDefault();
    });
  }
});