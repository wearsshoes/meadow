function sortTable(n, type) {
    var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
    table = document.getElementById("screenshotTable");
    switching = true;
    dir = "asc";
    
    // Remove existing sort indicators
    table.querySelectorAll('th').forEach(th => {
        th.classList.remove('asc', 'desc');
    });
    
    while (switching) {
        switching = false;
        rows = table.rows;
        
        for (i = 1; i < (rows.length - 1); i++) {
            shouldSwitch = false;
            x = rows[i].getElementsByTagName("TD")[n];
            y = rows[i + 1].getElementsByTagName("TD")[n];
            
            if (dir == "asc") {
                if ((type === 'timestamp' && new Date(x.innerHTML) > new Date(y.innerHTML)) ||
                    (type === 'text' && x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase())) {
                    shouldSwitch = true;
                    break;
                }
            } else if (dir == "desc") {
                if ((type === 'timestamp' && new Date(x.innerHTML) < new Date(y.innerHTML)) ||
                    (type === 'text' && x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase())) {
                    shouldSwitch = true;
                    break;
                }
            }
        }
        
        if (shouldSwitch) {
            rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
            switching = true;
            switchcount++;
        } else {
            if (switchcount == 0 && dir == "asc") {
                dir = "desc";
                switching = true;
            }
        }
    }
    
    // Add sort indicator
    table.getElementsByTagName('th')[n].classList.add(dir);
}
