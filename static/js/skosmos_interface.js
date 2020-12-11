                $(document).ready(function() {
                    var jsonResult = {};
                    var cvmUrl = "#{cvMgr.get(dsfv.datasetField.datasetFieldType.parentDatasetFieldType.name).getCvmUrl()}";
                    var cvmLang = "#{cvMgr.get(dsfv.datasetField.datasetFieldType.parentDatasetFieldType.name).getLanguage()}";
                    var cvmProtocol = "#{cvMgr.get(dsfv.datasetField.datasetFieldType.parentDatasetFieldType.name).getProtocol()}";
                    var cvmReqUrl = cvmUrl + "?protocol=" + cvmProtocol + "&amp;lang=" + cvmLang;
                    var vocabsize = "#{cvMgr.get(dsfv.datasetField.datasetFieldType.parentDatasetFieldType.name).getVocabs().size()}";
                    var readonly = "#{cvMgr.get(dsfv.datasetField.datasetFieldType.parentDatasetFieldType.name).isReadonly()}";
                    if (vocabsize == 1 &amp;&amp; readonly)
                        $("#akmi_#{valCount.index+1}_#{cvMgr.get(dsfv.datasetField.datasetFieldType.parentDatasetFieldType.name).getKeys()[0]}").find("input[name*='cv_vocabs_'").css('background-color' , '#EEEEEE');

                    var selectedVocab = "";
                    var vocabFieldValue = $("#akmi_#{valCount.index+1}_#{cvMgr.get(dsfv.datasetField.datasetFieldType.parentDatasetFieldType.name).getKeys()[0]}").find("input[name*='cv_vocabs_'").val();
                    if (vocabFieldValue =='' &amp;&amp; vocabsize == 1) {
                            selectedVocab = "#{cvMgr.get(dsfv.datasetField.datasetFieldType.parentDatasetFieldType.name).getVocabs()[0]}";
                            $("#akmi_#{valCount.index+1}_#{cvMgr.get(dsfv.datasetField.datasetFieldType.parentDatasetFieldType.name).getKeys()[0]}").find("input[name*='cv_vocabs_'").val(selectedVocab);
                    }
                    $("#akmi_#{valCount.index+1}_#{cvMgr.get(dsfv.datasetField.datasetFieldType.parentDatasetFieldType.name).getKeys()[0]}").find("input[name*='cv_vocabs_'").on("focusout", function(){
                          selectedVocab = $(this).val();
                        });

                   $("#akmi_#{valCount.index+1}_#{cvMgr.get(dsfv.datasetField.datasetFieldType.parentDatasetFieldType.name).getKeys()[1]}").find("input[name*='cv_term_']").autocomplete({
                        source: function(request, response) {
                            $.ajax({
                                url: cvmReqUrl + '&amp;vocab=' + selectedVocab,
                                dataType: "json",
                                data: { query: request.term},
                                success: function(data) {
                                    var results = data.results;
                                    var queries = [];
                                    var array = [];
                                    $.each(results, function(i, item) {
                                            queries.push(item.prefLabel);
                                        array.push({
                                            query: item.prefLabel,
                                            url: item.uri
                                        });
                                     });
                                    jsonResult = $.parseJSON(JSON.stringify(array));
                                    response(queries.sort());
                                }
                            });
                        },
                        minLength: 2,
                        select: function(event, ui) {
                            $.each(jsonResult, function(i, v) {
                                 if (v.query.search(new RegExp(ui.item.value)) != -1) {
                                     $("#akmi_#{valCount.index+1}_#{cvMgr.get(dsfv.datasetField.datasetFieldType.parentDatasetFieldType.name).getKeys()[2]}").find("input[name*='cv_url_']").val(v.url);
                                    return;
                                }
                            });
                         }
                    });
                 });
