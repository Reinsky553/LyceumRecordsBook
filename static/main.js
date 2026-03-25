document.addEventListener('DOMContentLoaded', () => {
    const leftPage = document.getElementById('leftPage');
    const rightPage = document.getElementById('rightPage');
    const leaf = document.getElementById('leaf');
    const leafFront = leaf.querySelector('.leaf-front');
    const leafBack = leaf.querySelector('.leaf-back');
    const nextBtn = document.getElementById('next');
    const prevBtn = document.getElementById('prev');
    const pageIndicator = document.getElementById('pageIndicator');
    const modal = document.getElementById("submitModal");
    const categorySelect = document.getElementById("categorySelect");
    const goHomeBtn = document.getElementById('goHome');
    const pageInput = document.getElementById('pageInput');
    const jumpBtn = document.getElementById('jumpBtn');

    let pagesData = [];
    let spreadIndex = 0;
    let isAnimating = false;

    async function loadBookData() {
        const response = await fetch('/api/get_pages');
        pagesData = await response.json();
        renderSpread();
    }

    async function updateCategories() {
        const response = await fetch('/api/get_categories');
        const categories = await response.json();
        if (categorySelect) {
            categorySelect.innerHTML = categories.map(c => `<option value="${c}">${c}</option>`).join('') + '<option value="other">Other...</option>';
        }
    }

    function getContent(idx) {
        if (idx < 0 || idx >= pagesData.length) return "";
        const title = pagesData[idx].title ? `<div class="title"><h2>${pagesData[idx].title}</h2></div>` : "";
        return `${title}<div class="content">${pagesData[idx].html}</div>`;
    }

    function renderSpread() {
        leftPage.innerHTML = getContent(spreadIndex * 2 - 1);
        rightPage.innerHTML = getContent(spreadIndex * 2);
    
        // Считает страницы
        const leftNum = spreadIndex * 2;
        const rightNum = spreadIndex * 2 + 1;
        const total = pagesData.length;

        // Индикатор страницы - правая страница
        if (rightNum <= total) {
            pageIndicator.innerText = `${rightNum} / ${total}`;
        } else {
            pageIndicator.innerText = `${leftNum} / ${total}`;
        }
    
        leaf.style.display = 'none';
        leaf.classList.remove('turn-forward');
        isAnimating = false;
    }

    async function next() {
        if (isAnimating || (spreadIndex * 2) >= pagesData.length - 1) return;
        isAnimating = true;
    
        leafFront.innerHTML = getContent(spreadIndex * 2); 
        leafBack.innerHTML = getContent(spreadIndex * 2 + 1);
    
        rightPage.innerHTML = getContent(spreadIndex * 2 + 2);
    
        leaf.style.display = 'block';
        leaf.offsetHeight; 
        leaf.classList.add('turn-forward');
    
        setTimeout(() => {
            spreadIndex++;
            renderSpread(); 
        }, 800);
    }

    async function prev() {
        if (isAnimating || spreadIndex === 0) return;
        isAnimating = true;
    
        leafBack.innerHTML = getContent(spreadIndex * 2 - 1);
        leafFront.innerHTML = getContent((spreadIndex - 1) * 2);
    
        leftPage.innerHTML = getContent((spreadIndex - 1) * 2 - 1);
    
        leaf.classList.add('turn-forward');
        leaf.style.display = 'block';
        leaf.offsetHeight; 
        leaf.classList.remove('turn-forward');
    
        setTimeout(() => {
            spreadIndex--;
            renderSpread();
        }, 800);
    }

    function jumpToCategory(categoryName) {
        const targetIndex = pagesData.findIndex(p => 
            p.html.includes(`<h1>${categoryName}</h1>`) && 
            p.html.includes('category-title-page')
        );
    
        if (targetIndex !== -1) {
            spreadIndex = Math.floor((targetIndex + 1) / 2);
            renderSpread();
        }
    }

    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('toc-link')) {
            const catName = e.target.getAttribute('data-target');
            jumpToCategory(catName);
        }
    });

    nextBtn.onclick = next;
    prevBtn.onclick = prev;
    
    if(document.getElementById("openSubmit")) {
        document.getElementById("openSubmit").onclick = () => modal.style.display = "block";
    }
    
    const closeBtn = document.querySelector(".close");
    if(closeBtn) closeBtn.onclick = () => modal.style.display = "none";

    goHomeBtn.onclick = () => {
        spreadIndex = 1; 
        renderSpread();
    };

    jumpBtn.onclick = () => {
        const pageNum = parseInt(pageInput.value);
        if (!isNaN(pageNum) && pageNum > 0 && pageNum <= pagesData.length) {
            spreadIndex = Math.floor(pageNum / 2);
            renderSpread();
        }
    };

    loadBookData();
    updateCategories();

    document.getElementById('userSubmitForm').onsubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        
        // Посылает данные в бэк
        const response = await fetch('/submit_entry', { 
            method: 'POST', 
            body: formData 
        });
        
        const result = await response.json();
        
        if(result.status === 'success') {
            alert("Ваше предложение отправлено на модерацию!");
            modal.style.display = "none";
            e.target.reset();
        }
    };
});