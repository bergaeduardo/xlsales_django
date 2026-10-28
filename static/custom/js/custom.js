/* ============================================================
   XLSales — Custom JS
   Inicialización global de plugins frontend (Tabler + ecosistema)
   ============================================================ */
(function ($) {
  "use strict";

  /* ── DataTables (idioma español, tema Tabler) ──────────────
     Cualquier <table class="datatable"> queda auto-inicializada.
  */
  if ($.fn && $.fn.DataTable) {
    $.extend(true, $.fn.dataTable.defaults, {
      language: {
        sProcessing: "Procesando…",
        sLengthMenu: "Mostrar _MENU_ registros",
        sZeroRecords: "No se encontraron resultados",
        sEmptyTable: "Sin datos disponibles",
        sInfo: "Mostrando _START_ a _END_ de _TOTAL_ registros",
        sInfoEmpty: "Mostrando 0 a 0 de 0 registros",
        sInfoFiltered: "(filtrado de _MAX_ registros)",
        sSearch: "Buscar:",
        sLoadingRecords: "Cargando…",
        oPaginate: {
          sFirst: "Primero",
          sLast: "Último",
          sNext: "Siguiente",
          sPrevious: "Anterior",
        },
        oAria: {
          sSortAscending: ": ordenar ascendente",
          sSortDescending: ": ordenar descendente",
        },
      },
      pageLength: 25,
      lengthMenu: [10, 25, 50, 100],
      responsive: true,
      autoWidth: false,
      dom:
        "<'row align-items-center'<'col-sm-12 col-md-6'l><'col-sm-12 col-md-6'f>>" +
        "<'row'<'col-sm-12'tr>>" +
        "<'row align-items-center'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'p>>",
    });
  }

  /* ── Select2 (tema Bootstrap 5, compatible Tabler) ─────────
     Cualquier <select class="select2"> queda auto-inicializado.
  */
  if ($.fn && $.fn.select2) {
    $.fn.select2.defaults.set("theme", "bootstrap-5");
    $.fn.select2.defaults.set("language", "es");
    $.fn.select2.defaults.set("width", "100%");
    $.fn.select2.defaults.set("placeholder", "Seleccionar…");

    $(function () {
      $("select.select2").select2();
    });
  }

  /* ── SweetAlert2 (colores Tabler) ──────────────────────────
     Helpers globales window.confirmDialog y window.toastSuccess/Error.
  */
  if (window.Swal) {
    window.confirmDialog = function (opts) {
      return window.Swal.fire(
        Object.assign(
          {
            icon: "question",
            title: "¿Confirmar?",
            showCancelButton: true,
            confirmButtonText: "Confirmar",
            cancelButtonText: "Cancelar",
            confirmButtonColor: "#206bc4",
            cancelButtonColor: "#626976",
            reverseButtons: true,
          },
          opts || {}
        )
      );
    };

    const Toast = window.Swal.mixin({
      toast: true,
      position: "top-end",
      showConfirmButton: false,
      timer: 3500,
      timerProgressBar: true,
    });
    window.toastSuccess = function (msg) {
      Toast.fire({ icon: "success", title: msg });
    };
    window.toastError = function (msg) {
      Toast.fire({ icon: "error", title: msg });
    };
  }

  /* ── Mensajes Django → toasts automáticos ─────────────────
     El template base emite window._djangoMessages = [...] antes
     de cargar los scripts. Los mostramos aquí cuando Swal está listo.
  */
  if (window.Swal && window._djangoMessages && window._djangoMessages.length) {
    var DjToast = window.Swal.mixin({
      toast: true,
      position: "top-end",
      showConfirmButton: false,
      timer: 5000,
      timerProgressBar: true,
    });
    var _tagIcon = { error: "error", success: "success", warning: "warning", info: "info" };
    window._djangoMessages.forEach(function (m, i) {
      setTimeout(function () {
        DjToast.fire({ icon: _tagIcon[m.tags] || "info", title: m.text });
      }, i * 400);
    });
  }

  /* ── Spinner al enviar forms de filtro ─────────────────────
     Aplica a cualquier <form method="get"> con botón submit
     que NO tenga el atributo data-no-spinner.
  */
  $(function () {
    $("form[method='get']").on("submit", function () {
      var $btn = $(this).find("button[type='submit']").not("[data-no-spinner]").first();
      if ($btn.length) {
        $btn.prop("disabled", true).html(
          '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>Cargando…'
        );
      }
    });
  });

  /* ── Filas de tabla clickeables (data-href) ────────────────
     Cualquier <tr data-href="..."> en un tbody navega al href
     al hacer clic, excepto sobre <a>, <button> o dtr-control.
  */
  $(function () {
    $("tbody").on("click", "tr[data-href]", function (e) {
      if (!$(e.target).closest("a, button, td.dtr-control").length) {
        window.location.href = $(this).data("href");
      }
    });
    $("tbody tr[data-href]").css("cursor", "pointer");
  });

  /* ── Filtro sticky + DataTables init ───────────────────────
     Bloque combinado para medir alturas antes de inicializar DataTables.
  */
  $(function () {
    var navbarEl = document.querySelector("header.navbar");
    var navbarPos = navbarEl ? window.getComputedStyle(navbarEl).position : "";
    var navbarH = (navbarPos === "sticky" || navbarPos === "fixed")
      ? ($(navbarEl).outerHeight() || 0)
      : 0;

    var $filterCard = $(".page-body .card").filter(function () {
      return $(this).find("form[method='get']").length > 0;
    }).first();
    var filterCardH = 0;
    if ($filterCard.length) {
      filterCardH = $filterCard.outerHeight() || 0;
      $filterCard.css({ position: "sticky", top: navbarH + "px", "z-index": 1027 });
    }

    if ($.fn && $.fn.DataTable) {
      $("table.datatable").each(function () {
        if (!$.fn.DataTable.isDataTable(this)) {
          var opts = {};

          if ($(this).hasClass("table-sticky-dt")) {
            var availH = Math.max(250, window.innerHeight - navbarH - filterCardH - 200);
            opts.scrollY  = availH + "px";
            opts.scrollX  = true;
            opts.scrollCollapse = true;
            opts.deferRender    = true;
            opts.responsive     = false;
          }

          $(this).DataTable(opts);
        }
      });

      $(window).on("resize.dtStickyResize", function () {
        $("table.datatable.table-sticky-dt").each(function () {
          if ($.fn.DataTable.isDataTable(this)) {
            var availH = Math.max(250, window.innerHeight - navbarH - filterCardH - 200);
            var dt = $(this).DataTable();
            dt.settings()[0].oScroll.sY = availH + "px";
            dt.columns.adjust();
          }
        });
      });
    }
  });

  /* ── Atajos de teclado ──────────────────────────────────────
     Alt+F → foco al primer campo del form de filtros
     Ctrl+Enter → submit del form de filtros desde cualquier campo
  */
  $(function () {
    $(document).on("keydown", function (e) {
      if (e.altKey && (e.key === "f" || e.key === "F")) {
        e.preventDefault();
        $("form[method='get']").find("input:visible, select:visible").first().focus();
      }
    });

    $("form[method='get']").on("keydown", "input, select, textarea", function (e) {
      if (e.ctrlKey && e.key === "Enter") {
        $(this).closest("form").submit();
      }
    });
  });

})(window.jQuery);
